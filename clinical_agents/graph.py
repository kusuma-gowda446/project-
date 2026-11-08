from typing import List, Optional
from langgraph.graph import StateGraph, START, END
from clinical_agents.core.state import ClinicalState
from clinical_agents.pipelines.ingestion import EHRDataPipeline
from clinical_agents.agents.base import BaseSpecialistAgent
from clinical_agents.agents.orchestrator import ClinicalOrchestrator


def build_clinical_graph(
    specialists: List[BaseSpecialistAgent],
    orchestrator: Optional[ClinicalOrchestrator] = None,
    db_path: str = "synthea_data.db"
):
    """
    Constructs the dynamic LangGraph execution DAG.
    
    Architecture:
      [START] 
         │
         ▼
     [Ingestion Pipeline]
         │
         ├───────────────────┬────────────────────┐
         ▼                   ▼                    ▼
    [Specialist 1]     [Specialist 2]       [Specialist 3]  <-- Fan-out (Parallel)
         │                   │                    │
         └───────────────────┼────────────────────┘
                             ▼
                    [Lead Orchestrator]                     <-- Fan-in (Consensus)
                             │
                             ▼
                           [END]
    """
    orchestrator = orchestrator or ClinicalOrchestrator()
    pipeline = EHRDataPipeline(db_path=db_path)

    workflow = StateGraph(ClinicalState)

    # 1. Ingestion Node
    def ingest_node(state: ClinicalState):
        pid = state["patient_id"]
        chart = pipeline.fetch_patient_chart(pid)
        chart_dict = chart.model_dump() if chart else None
        return {
            "patient_chart": chart_dict,
            "audit_log": [f"[IngestionPipeline] Fetched EHR chart for patient: {pid}"]
        }

    workflow.add_node("ingestion", ingest_node)

    # 2. Specialist Nodes (Dynamic Fan-out)
    specialist_node_names = []
    for spec in specialists:
        node_name = spec.name
        specialist_node_names.append(node_name)
        workflow.add_node(node_name, spec.as_node())

    # 3. Lead Orchestrator Node
    workflow.add_node("orchestrator", orchestrator.as_node())

    # 4. Define Graph Edges
    workflow.add_edge(START, "ingestion")

    # Fan-out: Ingestion connects to every specialist
    for node_name in specialist_node_names:
        workflow.add_edge("ingestion", node_name)

    # Fan-in: Every specialist connects to Orchestrator
    for node_name in specialist_node_names:
        workflow.add_edge(node_name, "orchestrator")

    # Orchestrator connects to END
    workflow.add_edge("orchestrator", END)

    # Compile the graph
    app = workflow.compile()
    return app
