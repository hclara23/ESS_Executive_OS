export const mockApprovals = [
  {
    id: "appr-1024",
    title: "Send pricing update to Northstar Electric",
    risk: "medium",
    status: "pending",
    domain: "WORK",
    requestedBy: "Alex Sanchez",
    summary: "Price adjustment for Q1 bulk supply renewal.",
  },
  {
    id: "appr-1025",
    title: "Approve overtime for warehouse team",
    risk: "high",
    status: "pending",
    domain: "WORK",
    requestedBy: "Sandra Sanchez",
    summary: "Overtime required to cover inbound shipment surge.",
  },
];

export const mockTasks = [
  {
    id: "task-901",
    title: "Prepare client QBR deck",
    due: "Today 3:00 PM",
    owner: "Alex Sanchez",
    priority: "High",
  },
  {
    id: "task-902",
    title: "Review payroll adjustments",
    due: "Tomorrow 10:00 AM",
    owner: "Sandra Sanchez",
    priority: "Medium",
  },
  {
    id: "task-903",
    title: "Follow up with Apex Lighting",
    due: "Friday 4:00 PM",
    owner: "Alex Sanchez",
    priority: "Medium",
  },
];

export const mockBriefing = {
  schedule: [
    { time: "8:30 AM", title: "Vendor check-in" },
    { time: "10:00 AM", title: "Pipeline review" },
    { time: "1:00 PM", title: "HR weekly sync" },
  ],
  priorities: [
    "Finalize renewal proposal for Northstar Electric",
    "Review Q1 hiring plan",
    "Close open approvals in finance",
  ],
  opportunities: [
    "New project request from Beacon Builders",
    "Vendor pricing lock-in expiring in 7 days",
  ],
};
