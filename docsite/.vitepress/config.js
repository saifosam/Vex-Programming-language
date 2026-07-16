// Vex documentation site config
export default {
  base: "/Vex-Programming-language/",
  title: "Vex",
  description: "A tiny Python-based DSL for building styled desktop apps",

  head: [
    ["link", { rel: "icon", type: "image/png", href: "/Vex-Programming-language/favicon.png" }],
    [
      "style",
      {},
      `
      :root {
        --vp-c-brand-1: #f97316;
        --vp-c-brand-2: #ea580c;
        --vp-c-brand-3: #c2410c;
        --vp-c-brand-soft: rgba(249, 115, 22, 0.14);
        --vp-button-brand-bg: #f97316;
        --vp-button-brand-hover-bg: #ea580c;
        --vp-button-brand-active-bg: #c2410c;
        --vp-c-tip-bg: rgba(249, 115, 22, 0.1);
        --vp-c-tip-text: #f97316;
        --vp-home-hero-name-color: transparent;
        --vp-home-hero-name-background: linear-gradient(135deg, #f97316 0%, #fb923c 50%, #fdba74 100%);
      }
      .dark {
        --vp-c-brand-1: #fb923c;
        --vp-c-brand-2: #f97316;
        --vp-c-brand-3: #ea580c;
        --vp-c-brand-soft: rgba(251, 146, 60, 0.16);
      }
      `,
    ],
  ],

  themeConfig: {
    logo: "/Vex-Programming-language/favicon.png",

    nav: [
      { text: "Home", link: "/" },
      { text: "Guide", link: "/guide/getting-started" },
      { text: "Examples", link: "/examples" },
    ],

    sidebar: [
      {
        text: "Guide",
        items: [
          { text: "Getting Started", link: "/guide/getting-started" },
          { text: "Language Spec", link: "/guide/language-spec" },
          { text: "Design", link: "/guide/design" },
        ],
      },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/saifosam/Vex-Programming-language" },
    ],
  },
};
