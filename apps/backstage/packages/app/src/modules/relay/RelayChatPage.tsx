import { configApiRef, useApi } from '@backstage/core-plugin-api';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles({
  frame: {
    border: 0,
    display: 'block',
    height: 'calc(100vh - 48px)',
    width: '100%',
  },
});

export const RelayChatPage = () => {
  const config = useApi(configApiRef);
  const embedUrl =
    config.getOptionalString('relay.chatEmbedUrl') ?? 'http://localhost:3000';
  const classes = useStyles();

  return (
    <iframe
      className={classes.frame}
      src={embedUrl}
      title="Relay Assistant"
    />
  );
};
