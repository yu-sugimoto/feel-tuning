import 'dotenv/config';

export default {
  expo: {
    name: 'music-swipe',
    slug: 'music-swipe',
    extra: {
      API_URL: process.env.API_URL,
    },
  },
};
