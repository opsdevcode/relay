import { createApp } from '@backstage/frontend-defaults';
import catalogPlugin from '@backstage/plugin-catalog/alpha';
import scaffolderPlugin from '@backstage/plugin-scaffolder/alpha';
import techdocsPlugin from '@backstage/plugin-techdocs/alpha';
import { navModule } from './modules/nav';
import { relayChatPlugin } from './modules/relay';

export default createApp({
  features: [
    catalogPlugin,
    scaffolderPlugin,
    techdocsPlugin,
    relayChatPlugin,
    navModule,
  ],
});
