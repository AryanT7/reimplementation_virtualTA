export const chatbots = [
    {
      id: "virtual-ta",
      name: "Virtual TA",
      loginPath: "/virtual-ta/login",
      apiRoute: "/api/virtual-ta/chat",
      dashboardPath: "/virtual-ta/dashboard",
    },
    {
      id: "course-eval",
      name: "Course Evaluation Bot",
      loginPath: "/course-eval/login",
      apiRoute: "/api/course-eval/chat",
      dashboardPath: "/course-eval/dashboard",
    },
    // ── Add more bots here ─────────────────────────────────────
  ] as const;             // ← “as const” keeps strings literal
  
  
  /** Element type of the array above. */
  export type Chatbot = typeof chatbots[number];
  
  
  /** `"virtual-ta" | "course-eval" | …`  — auto-updates when you add a bot. */
  export type ChatbotID = Chatbot["id"];
  
  
  /**
   * Quick hash-map lookup:  chatbotConfigs["virtual-ta"] → full bot record.
   * Used by `import { chatbotConfigs } from "@/config/chatbots";`
   */
  export const chatbotConfigs: Record<ChatbotID, Chatbot> = chatbots.reduce(
    (acc, bot) => {
      acc[bot.id] = bot;
      return acc;
    },
    {} as Record<ChatbotID, Chatbot>
  );
  