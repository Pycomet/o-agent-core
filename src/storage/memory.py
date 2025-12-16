import threading
from typing import Dict, List
from datetime import datetime


class GovernanceStore:
    """Thread-safe in-memory store for governance notes keyed by proposal_id"""

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, str]]] = {}
        self._lock = threading.Lock()

    def add_note(self, proposal_id: str, note: str) -> None:
        """
        Add a governance note to a proposal.

        Args:
            proposal_id: Unique identifier for the proposal
            note: Text content of the note
        """
        with self._lock:
            if proposal_id not in self._store:
                self._store[proposal_id] = []

            self._store[proposal_id].append({
                "note": note,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

    def get_notes(self, proposal_id: str) -> List[Dict[str, str]]:
        """
        Retrieve all notes for a given proposal.

        Args:
            proposal_id: Unique identifier for the proposal

        Returns:
            List of note dictionaries with 'note' and 'timestamp' keys
        """
        with self._lock:
            return self._store.get(proposal_id, []).copy()

    def clear(self) -> None:
        """Clear all notes from the store (useful for testing)"""
        with self._lock:
            self._store.clear()


# Global instance for the application
governance_store = GovernanceStore()

