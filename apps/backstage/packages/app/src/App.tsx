import { createApp } from '@backstage/frontend-defaults';
import catalogPlugin from '@backstage/plugin-catalog/alpha';
import { navModule } from './modules/nav';
import { relayChatPlugin } from './modules/relay';

export default createApp({
  features: [catalogPlugin, relayChatPlugin, navModule],
});
