// AI Company 配置文件
// 修改此文件来自定义你的组织架构

const CONFIG = {
  // 公司名称
  companyName: "AI Company",
  subtitle: "组织架构与能力清单",

  // CEO 助理配置
  ceoAssistant: {
    name: "CEO 助理",
    id: "ceo-assistant",
    description: "永久驻留的 AI 调度器，保持上下文记忆",
    capabilities: ["滴答清单集成", "全平台发布权限", "永久 Session 记忆"]
  },

  // 部门配置
  departments: [
    {
      name: "内容与公关部",
      id: "content-pr-department",
      icon: "📢",
      color: "purple",
      categories: [
        {
          name: "素材收集",
          icon: "📥",
          skills: ["social-media-download", "perplexity-research"]
        },
        {
          name: "内容创作",
          icon: "✨",
          skills: ["nanobanana-draw", "speech-recognition", "video-chapter-nav"]
        },
        {
          name: "发布分发",
          icon: "📤",
          skills: ["social-media-publish"],
          note: "🔒 需审批"
        }
      ]
    },
    {
      name: "研发部",
      id: "dev-department",
      icon: "💻",
      color: "blue",
      categories: [
        {
          name: "移动端",
          icon: "📱",
          skills: ["eas-testflight"]
        },
        {
          name: "Web 端",
          icon: "🌐",
          skills: ["deploy-static"]
        }
      ]
    },
    {
      name: "产品部",
      id: "product-department",
      icon: "📦",
      color: "green",
      categories: [
        {
          name: "用户研究",
          icon: "🔍",
          skills: ["pain-point-research", "research-by-reddit", "perplexity-research"]
        }
      ]
    },
    {
      name: "战投部",
      id: "research-department",
      icon: "🔬",
      color: "amber",
      categories: [
        {
          name: "调研分析",
          icon: "📊",
          skills: ["perplexity-research", "research-by-reddit", "pain-point-research"]
        },
        {
          name: "投资研究",
          icon: "💰",
          skills: ["futu-trades"]
        }
      ]
    },
    {
      name: "情报分析部",
      id: "intelligence-department",
      icon: "🕵️",
      color: "red",
      categories: [
        {
          name: "线索追踪",
          icon: "🔎",
          skills: ["social-media-download", "perplexity-research"]
        }
      ]
    },
    {
      name: "运营部",
      id: "ops-department",
      icon: "📊",
      color: "cyan",
      categories: [
        {
          name: "日常运营",
          icon: "📈",
          skills: ["daily-review"]
        }
      ]
    },
    {
      name: "事业部",
      id: "business-unit",
      icon: "🏢",
      color: "indigo",
      categories: [
        {
          name: "从 0 到 1",
          icon: "🚀",
          skills: [],
          notes: ["包含产品部能力", "包含研发部能力"]
        }
      ]
    }
  ],

  // Skills 分类汇总
  skillCategories: [
    {
      name: "内容创作",
      skills: ["nanobanana-draw", "speech-recognition", "video-chapter-nav", "volc-tts"]
    },
    {
      name: "社媒发布",
      skills: ["social-media-publish", "social-media-download", "biliup-publish"]
    },
    {
      name: "调研分析",
      skills: ["perplexity-research", "research-by-reddit", "pain-point-research"]
    },
    {
      name: "开发部署",
      skills: ["eas-testflight", "deploy-static"]
    },
    {
      name: "数据工具",
      skills: ["chat-to-supabase", "futu-trades", "KOL-info-collect"]
    },
    {
      name: "效率工具",
      skills: ["pdf2markdown", "openrouter-chat"]
    },
    {
      name: "项目管理",
      skills: ["projects", "dida365-pomodoro"]
    },
    {
      name: "其他",
      skills: ["personal-assistant", "icloud-sync"]
    }
  ]
};
