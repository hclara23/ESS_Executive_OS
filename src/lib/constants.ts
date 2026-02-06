export const PERSONAS = [
  {
    id: "alex",
    name: "Alex Sanchez",
    focus: "Sales, pipeline, projects, client relationships",
  },
  {
    id: "sandra",
    name: "Sandra Sanchez",
    focus: "Admin, finance, HR, employee relations",
  },
] as const;

export const DOMAINS = ["WORK", "PERSONAL"] as const;
export type Domain = (typeof DOMAINS)[number];
export type Visibility = "personal_private" | "business_private" | "org_shared";
