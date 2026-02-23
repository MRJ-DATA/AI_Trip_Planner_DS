
from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition

from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool


from optimization.itinerary_optimizer import select_best_itinerary
from features.itinerary_features import extract_features
from models.satisfaction_model import predict_satisfaction


class GraphBuilder:
    def __init__(self, model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()

      
        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConverterTool()

        self.tools = [
            *self.weather_tools.weather_tool_list,
            *self.place_search_tools.place_search_tool_list,
            *self.calculator_tools.calculator_tool_list,
            *self.currency_converter_tools.currency_converter_tool_list
        ]

        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.system_prompt = SYSTEM_PROMPT
        self.graph = None

   
    def agent_function(self, state: MessagesState):
        """
        The agent:
        - understands the user request
        - calls tools
        - generates candidate itineraries (NOT final decision)
        """
        user_messages = state["messages"]
        input_messages = [self.system_prompt] + user_messages

        response = self.llm_with_tools.invoke(input_messages)

        return {
            "messages": [response]
        }

   
    def decision_engine(self, state: MessagesState):
        """
        This function represents YOUR contribution.
        It:
        - takes multiple candidate itineraries
        - extracts features
        - predicts satisfaction
        - selects the optimal itinerary
        """

        candidate_itineraries = state.get("candidate_itineraries", [])

        # Safety check
        if not candidate_itineraries:
            return state

        scored_itineraries = []

        for itinerary in candidate_itineraries:
            features = extract_features(itinerary)
            satisfaction_score = predict_satisfaction(features)

            scored_itineraries.append({
                "itinerary": itinerary,
                "satisfaction_score": satisfaction_score
            })

      
        best_itinerary = select_best_itinerary(scored_itineraries)

        state["best_itinerary"] = best_itinerary
        return state

    
    def build_graph(self):
        graph_builder = StateGraph(MessagesState)

        # Nodes
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("decision_engine", self.decision_engine)

        # Edges
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")

        # 🔥 Key change: decision happens AFTER agent reasoning
        graph_builder.add_edge("agent", "decision_engine")
        graph_builder.add_edge("decision_engine", END)

        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.build_graph()