export const getURL = () => {
  let url =
    process.env.NEXT_PUBLIC_SITE_URL ||
    process.env.NEXT_PUBLIC_APP_URL ||
    (typeof window !== 'undefined' && window.location.origin ? window.location.origin : '') ||
    'http://localhost:3000';

  url = url.includes('http') ? url : `https://${url}`;
  return url.endsWith('/') ? url.slice(0, -1) : url;
};
