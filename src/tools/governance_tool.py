"""Governance note tool for AI-led governance workflows"""

from typing import Dict, Any

from .base import BaseTool
from ..storage.memory import governance_store


class GovernanceNoteTool(BaseTool):
    """
    Tool for adding governance notes to proposals.

    Designed for AI-led organization workflows where the agent can
    document decisions, reviews, and actions on governance proposals.
    """

    @property
    def name(self) -> str:
        return "governance_note"

    @property
    def description(self) -> str:
        return "Add a governance note to a proposal. Used for documenting decisions, reviews, approvals, or other governance-related information."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "proposal_id": {
                    "type": "string",
                    "description": "Unique identifier for the proposal (e.g., 'proposal-123', 'gov-2024-001')",
                },
                "note": {
                    "type": "string",
                    "description": "The governance note content to add",
                },
            },
            "required": ["proposal_id", "note"],
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a governance note to a proposal.

        Args:
            params: Must contain 'proposal_id' and 'note' keys

        Returns:
            Dictionary confirming the note was added
        """
        proposal_id = params.get("proposal_id")
        note = params.get("note")

        if not proposal_id:
            raise ValueError("Missing required parameter: proposal_id")
        if not note:
            raise ValueError("Missing required parameter: note")

        if not isinstance(proposal_id, str):
            raise ValueError("proposal_id must be a string")
        if not isinstance(note, str):
            raise ValueError("note must be a string")

        if len(proposal_id.strip()) == 0:
            raise ValueError("proposal_id cannot be empty")
        if len(note.strip()) == 0:
            raise ValueError("note cannot be empty")

        # Add note to governance store
        governance_store.add_note(proposal_id.strip(), note.strip())

        # Get current note count for this proposal
        all_notes = governance_store.get_notes(proposal_id.strip())

        return {
            "success": True,
            "proposal_id": proposal_id.strip(),
            "note": note.strip(),
            "total_notes": len(all_notes),
        }
