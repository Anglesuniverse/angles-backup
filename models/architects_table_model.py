# models/architects_table_model.py

from datetime import datetime

class ArchitectDecision:
    def __init__(
        self,
        decision_type: str,
        decision_summary: str,
        agent_involved: str,
        summary: str,
        full_description: str,
        decision_by: str,
        source_of_decision: str,
        decision_category: str,
        decision_scope: str,
        impact_level: str,
        related_agent_or_module: str,
        created_at: datetime = None,
    ):
        self.decision_type = decision_type
        self.decision_summary = decision_summary
        self.agent_involved = agent_involved
        self.summary = summary
        self.full_description = full_description
        self.decision_by = decision_by
        self.source_of_decision = source_of_decision
        self.decision_category = decision_category
        self.decision_scope = decision_scope
        self.impact_level = impact_level
        self.related_agent_or_module = related_agent_or_module
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "decision_type": self.decision_type,
            "decision_summary": self.decision_summary,
            "agent_involved": self.agent_involved,
            "summary": self.summary,
            "full_description": self.full_description,
            "decision_by": self.decision_by,
            "source_of_decision": self.source_of_decision,
            "decision_category": self.decision_category,
            "decision_scope": self.decision_scope,
            "impact_level": self.impact_level,
            "related_agent_or_module": self.related_agent_or_module,
            "created_at": self.created_at.isoformat(),
        }