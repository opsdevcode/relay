import {
  createFrontendPlugin,
  PageBlueprint,
} from '@backstage/frontend-plugin-api';
import ChatIcon from '@material-ui/icons/Chat';
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

export const relayChatPlugin = createFrontendPlugin({
  pluginId: 'relay-chat',
  title: 'Relay Assistant',
  extensions: [relayChatPage],
});
