import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';
import { getURL } from '@/lib/url';

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const next = requestUrl.searchParams.get('next') ?? '/dashboard';
  const baseUrl = getURL();

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      // Check if profile exists, create if not
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data: existingProfile } = await supabase
          .from('profiles')
          .select('id')
          .eq('id', user.id)
          .single();

        if (!existingProfile) {
          await supabase.from('profiles').insert({
            id: user.id,
            email: user.email || '',
            first_name: user.user_metadata?.full_name?.split(' ')[0] || null,
            last_name: user.user_metadata?.full_name?.split(' ').slice(1).join(' ') || null,
            profile_photo_url: user.user_metadata?.avatar_url || null,
            is_profile_complete: false,
          });
        }
      }
      return NextResponse.redirect(`${baseUrl}${next}`);
    }
  }

  return NextResponse.redirect(`${baseUrl}/login?error=auth_callback_error`);
}
