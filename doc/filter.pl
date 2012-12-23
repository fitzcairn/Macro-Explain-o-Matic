#!/usr/bin/perl


my $fh;
my $all = join('', <STDIN>);

# Filter out macros.
while ($all =~ m/\<pre\>(.+?)\<\/pre\>/sg) {
  my $macro = $1;

  # Filter out HTML
  $macro =~ s/\<.+?\>(.+?)\<\.+?\>/$1/g;

  # Last-ditch test
  if ($macro !~ m/<.+>/) {
    print $macro."\n\n";
  }
}

