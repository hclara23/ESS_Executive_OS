import os
from Brain.AI_Brain import ReplyBrain
from Features.Face.Mouth import speak
from Features.MemoryStore import add_private_memory

class GhostWriter:
    def __init__(self):
        self.brain = ReplyBrain()

    def generate_proactive_draft(self, user, context_type, context_data):
        """
        Revolutionary Phase 3: Proactively draft content based on upcoming milestones.
        """
        prompt = f"As ELIO, the executive agent for {user}, draft a professional response for a {context_type}. " \
                 f"Context: {context_data}. Keep it concise and action-oriented."
        
        draft = self.brain.generate_reply(prompt)
        
        # Save to memory as a staged action
        add_private_memory(user, f"Ghost-Writer drafted a {context_type}: {draft[:100]}...", tags=["ghostwriter", "draft", context_type])
        
        print(f"[Ghost-Writer] Staged draft for {context_type}")
        return draft

ghost_writer = GhostWriter()
