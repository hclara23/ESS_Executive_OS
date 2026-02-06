"use client";

import { create } from "zustand";

export type PersonaId = "alex" | "sandra";
export type Domain = "WORK" | "PERSONAL";
export type Role = "owner" | "admin" | "member";

type SessionState = {
  role: Role;
  activePersona: PersonaId;
  domain: Domain;
  allowPersonalInWork: boolean;
  setRole: (role: Role) => void;
  setPersona: (persona: PersonaId) => void;
  setDomain: (domain: Domain) => void;
  togglePersonalInWork: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  role: "owner",
  activePersona: "alex",
  domain: "WORK",
  allowPersonalInWork: false,
  setRole: (role) => set({ role }),
  setPersona: (activePersona) => set({ activePersona }),
  setDomain: (domain) => set({ domain }),
  togglePersonalInWork: () =>
    set((state) => ({ allowPersonalInWork: !state.allowPersonalInWork })),
}));
