// Vex documentation site config
export default {
  base: "/Vex-Programming-language/",
  title: "Vex",
  description: "A tiny Python-based DSL for building styled desktop apps",
  themeConfig: {
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
