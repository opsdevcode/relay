import {
  createFrontendPlugin,
  PageBlueprint,
} from '@backstage/frontend-plugin-api';
import ChatIcon from '@material-ui/icons/Chat';
import ShowChartIcon from '@material-ui/icons/ShowChart';
import { createElement } from 'react';

const relayChatPage = PageBlueprint.make({
  name: 'relay-chat',
  params: {
    path: '/relay',
    title: 'Relay Assistant',
    icon: createElement(ChatIcon, { fontSize: 'inherit' }),
    noHeader: true,
    loader: () =>
      import('./RelayChatPage').then(m => createElement(m.RelayChatPage)),
  },
});

const observabilityPage = PageBlueprint.make({
  name: 'observability',
  params: {
    path: '/observability',
    title: 'Observability',
    icon: createElement(ShowChartIcon, { fontSize: 'inherit' }),
    noHeader: true,
    loader: () =>
      import('./GrafanaEmbedPage').then(m => createElement(m.GrafanaEmbedPage)),
  },
});

export const relayChatPlugin = createFrontendPlugin({
  pluginId: 'relay-chat',
  title: 'Relay Assistant',
  extensions: [relayChatPage, observabilityPage],
});
