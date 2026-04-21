import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Chappi AI Office',
  tagline: 'Your personal AI office — Telegram-first, always-on, self-hosted',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'http://80.74.25.43',
  baseUrl: '/',
  organizationName: 'sidnevart',
  projectName: 'chappi-ai-office',

  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/sidnevart/chappi-ai-office/tree/main/docs-site/',
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl:
            'https://github.com/sidnevart/chappi-ai-office/tree/main/docs-site/',
          // Useful options to enforce blogging best practices
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Chappi AI Office',
      logo: {
        alt: 'Chappi AI Office',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'ownerManual',
          position: 'left',
          label: 'Owner Manual',
        },
        {
          type: 'docSidebar',
          sidebarId: 'setupGuide',
          position: 'left',
          label: 'Setup Guide',
        },
        {
          href: 'https://80.74.25.43/',
          label: '🏢 Office UI',
          position: 'right',
        },
        {
          href: 'http://80.74.25.43:4000',
          label: '📊 Grafana',
          position: 'right',
        },
        {
          href: 'https://github.com/sidnevart/chappi-ai-office',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Owner Manual', to: '/docs/owner-manual/intro'},
            {label: 'Setup Guide', to: '/docs/setup-guide/prerequisites'},
          ],
        },
        {
          title: 'Dashboards',
          items: [
            {label: '🏢 Office UI', href: 'https://80.74.25.43/'},
            {label: '📊 Grafana', href: 'http://80.74.25.43:4000'},
          ],
        },
        {
          title: 'More',
          items: [
            {label: 'GitHub', href: 'https://github.com/sidnevart/chappi-ai-office'},
          ],
        },
      ],
      copyright: `Built with ❤️ by @sidnevart · Chappi AI Office`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
