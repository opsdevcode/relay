import { configApiRef, useApi } from '@backstage/core-plugin-api';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import { useEffect, useState } from 'react';

const useStyles = makeStyles({
  frame: {
    border: 0,
    display: 'block',
    height: 'calc(100vh - 48px)',
    width: '100%',
  },
  placeholder: {
    padding: 24,
  },
});

type GrafanaEmbedPayload = {
  configured?: boolean;
  url?: string;
  hint?: string;
  service?: string;
};

export const GrafanaEmbedPage = () => {
  const config = useApi(configApiRef);
  const apiBase =
    config.getOptionalString('relay.apiBaseUrl') ?? 'http://localhost:8080';
  const overrideUrl = config.getOptionalString('relay.observabilityEmbedUrl');
  const classes = useStyles();
  const [embed, setEmbed] = useState<GrafanaEmbedPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (overrideUrl) {
      setEmbed({ configured: true, url: overrideUrl });
      return;
    }
    fetch(`${apiBase}/platform-services`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(services => {
        const obs = services.find(
          (s: { id?: string }) => s.id === 'observability-insight',
        );
        const payload = obs?.view_urls?.grafana_embed as
          | GrafanaEmbedPayload
          | undefined;
        setEmbed(payload ?? null);
      })
      .catch(err => setError(String(err)));
  }, [apiBase, overrideUrl]);

  if (overrideUrl || (embed?.configured && embed.url)) {
    const src = overrideUrl ?? embed?.url ?? '';
    return (
      <iframe className={classes.frame} src={src} title="Grafana observability" />
    );
  }

  return (
    <div className={classes.placeholder}>
      <Typography variant="h5" gutterBottom>
        Observability (Grafana embed)
      </Typography>
      {error ? (
        <Typography color="error">Could not load embed URL: {error}</Typography>
      ) : (
        <Typography color="textSecondary">
          {embed?.hint ??
            'Configure GRAFANA_BASE_URL on the Relay API or set relay.observabilityEmbedUrl in app-config.'}
        </Typography>
      )}
    </div>
  );
};
