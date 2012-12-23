#!/usr/bin/perl

# Take in a lua data  file, and convert it into csv.

use strict;
use File::Find;
use File::Spec;
use File::Spec::Functions;
use Data::Dumper;

# Predeclare subs
sub trim($);
sub fprint($$);
sub handle_item($);
sub handle_spell($);
sub test($);
sub cleanup();


# Get src and dest
die("Usage: $0 <src> <dest> [1 for dry run]\n")
  unless (defined $ARGV[0] && -e $ARGV[0] && defined $ARGV[1] && -e $ARGV[1]);

my $src_file   = File::Spec->rel2abs($ARGV[0]);
my $dst_dir    = File::Spec->rel2abs($ARGV[1]);
my $dryrun     = $ARGV[2];

# Create filenames
my $dst_s_file = File::Spec->catfile( ($dst_dir), "spells.csv");
my $dst_i_file = File::Spec->catfile( ($dst_dir), "items.csv");


my $i_fh;
my $o_s_fh;
my $o_i_fh;
open($i_fh, $src_file)    or die "Couldn't open $src_file: $!";
open($o_s_fh, ">$dst_s_file") or die "Couldn't open $dst_s_file: $!" if not $dryrun;
open($o_i_fh, ">$dst_i_file") or die "Couldn't open $dst_i_file: $!" if not $dryrun;

# Spell data accumulator.
my %g_spells = ();

# Slot translation: internal global id -> inventory slot id.
# INVSLOT_AMMO       = 0;
# INVSLOT_HEAD       = 1; INVSLOT_FIRST_EQUIPPED = INVSLOT_HEAD;
# INVSLOT_NECK       = 2;
# INVSLOT_SHOULDER   = 3;
# INVSLOT_BODY       = 4;
# INVSLOT_CHEST      = 5;
# INVSLOT_WAIST      = 6;
# INVSLOT_LEGS       = 7;
# INVSLOT_FEET       = 8;
# INVSLOT_WRIST      = 9;
# INVSLOT_HAND       = 10;
# INVSLOT_FINGER1        = 11;
# INVSLOT_FINGER2        = 12;
# INVSLOT_TRINKET1   = 13;
# INVSLOT_TRINKET2   = 14;
# INVSLOT_BACK       = 15;
# INVSLOT_MAINHAND   = 16;
# INVSLOT_OFFHAND        = 17;
# INVSLOT_RANGED     = 18;
# INVSLOT_TABARD     = 19;
my %g_slot_map = (
                  '"INVTYPE_2HWEAPON",' => [16, 17],
                  '"INVTYPE_CHEST",'    => [5],
                  '"INVTYPE_CLOAK",'    => [15],
                  '"INVTYPE_FEET",'     => [8],
                  '"INVTYPE_HAND",'     => [10],
                  '"INVTYPE_HOLDABLE",' => [16],
                  '"INVTYPE_LEGS",'     => [7],
                  '"INVTYPE_RANGED",'   => [18],
                  '"INVTYPE_RANGEDRIGHT",' => [18],
                  '"INVTYPE_ROBE",'        => [5],
                  '"INVTYPE_SHIELD",'      => [17],
                  '"INVTYPE_THROWN",'      => [18],
                  '"INVTYPE_WEAPON",'      => [16, 17],
                  '"INVTYPE_WEAPONMAINHAND",' => [16],
                  '"INVTYPE_WEAPONOFFHAND",'  => [17],
                  '"INVTYPE_AMMO",' => [0],
                  '"INVTYPE_BODY",' => [4],
                  '"INVTYPE_FINGER",' => [11, 12],
                  '"INVTYPE_HEAD",' => [1],
                  '"INVTYPE_NECK",' => [2],
                  '"INVTYPE_RELIC",' => [17],
                  '"INVTYPE_SHOULDER",' => [3],
                  '"INVTYPE_TABARD",' => [19],
                  '"INVTYPE_TRINKET",' => [13, 14],
                  '"INVTYPE_WAIST",' => [6],
                  '"INVTYPE_WRIST",' => [9],
                 );

# Read in each line, transform, and write out.
my $line;
my @accum  = ();
my $items  = 0;
my $spells = 1;
while($line = readline($i_fh)) {
  chomp($line);

  $line   =~ s/^DataDumperSpells.+$//; # Dump header
  $items  = $items || ($line =~ s/^DataDumperItems.+$//);  # Dump header
  $spells = !$items;
  next unless $line;

  $line =~ s/ --.*$//;                # Remove comments
  $line =~ s/\s*\[\"(\d+)\"\]\ \= \{.*//; # Dump lua table key
  $line =~ s/\s+/\ /g;               # Normalize spaces
  $line =~ s/\".+\\\\/\"/;           # Strip icon dir
  $line =~ s/\\\"/\"\"/g;            # Handle embedded quotes
  $line =~ s/^\s+true,/ \"True\",/g;
  $line =~ s/^\s+false,/ \"False\",/g;   # Booleans


  # Done creating entry?  Push
  if ($line =~ s/^\s*}.*$//) {
    #print("$items   $spells\n");
    if ($items) {
      handle_item(\@accum);
    } else {
      handle_spell(\@accum);
    }
    @accum = ();
  }
  else {
    push(@accum, $line) if test($line);
  }
}

# Done
cleanup();


# ---- Subs ----

# Helper to test for non-space in string.
sub test($) {
  my $s = shift;
  return ($s =~ /\S/);
}


# Perl trim function to remove whitespace from the start and end of
# the string
sub trim($)
{
	my $string = shift;
	$string =~ s/^ +//;
	$string =~ s/ +$//;

    # Extra: shift "" to empty
    $string =~ s/^"",$/,/;

	return $string;
}

# Handle dryruns, output to file
# Takes array of fields + fh
sub fprint($$) {
  my $accum = shift;
  my $fh  = shift;

  my $out = join('', @{$accum});
  $out =~ s/,$//;   # Strip trailing ','
  $out = $out."\n";

  print $out;
  print $fh $out if not $dryrun;
}

# Interpret item lines to convert slot type and multiplex output.
sub handle_item($) {
  my $accum_ref = shift;
  my $line = "";

  # Parse
  my @accum = map(trim($_), @{$accum_ref});
  return unless scalar(@accum) > 0;

  # Translate slot
  #print($accum[8]."\n");
  if ($g_slot_map{$accum[8]}) {
    $accum[8] = join("-", @{$g_slot_map{$accum[8]}}).",";
  } else {
    $accum[8] = ',';
  }


  # Output two lines; one with name the other with item:slot as the name.
  # Unshift on the key field, which to start is the item:id.
  my $name = $accum[0];
  my $id   = $accum[11];
  unshift(@accum, "item:".$id);
  fprint(\@accum, $o_i_fh);

  # Now add a line with the key being the name of the item.
  $accum[0] = $name;
  fprint(\@accum, $o_i_fh);
}

# Spells
sub handle_spell($) {
  my $accum_ref = shift;
  my @accum = map(trim($_), @{$accum_ref});
  return unless scalar(@accum) > 0;

  # Output three lines: one with the name, and two with
  # different spacing for ranks.
  my ($name) = ($accum[1] =~ m/\"(.+?)\",/);
  my ($rank) = ($accum[2] =~ m/([\w ]+)/);

  # Deal with three variations of named id.
  my @keys = ("\"$name\",");
  @keys    = ("\"$name\",", "\"$name ($rank)\",", "\"$name($rank)\",") if $rank;

  foreach my $key (@keys) {
    # Make a new array for each key.
    my @accum = map(trim($_), @{$accum_ref});
    unshift(@accum, $key);

    # Possibly save, dealing with collisions
    if (!defined($g_spells{$key})) {
      $g_spells{$key} = \@accum;
    }
    # Collision!  Decide what to keep.
    else {
      my $old = $g_spells{$key};

      # If the new spell has a rank and the old one does not,
      # save the new one.
      if (test($accum[3]) && !test($old->[3])) {
        $g_spells{$key} = \@accum;
        next;
      }

      # if rank(new) > rank(old), save.
      if (test($accum[3]) && test($old->[3])) {
        my ($new_rank) = ($accum[3] =~ m/(\d+)/);
        my ($old_rank) = ($old->[3] =~ m/(\d+)/);
        if ($new_rank > $old_rank) {
          $g_spells{$key} = \@accum;
          next;
        }
      }

      # Ok, no ranks, and name collision.  Save the one with a mana
      # cost if possible.
      if (test($accum[5]) || test($old->[5])) {
        my ($new_c) = ($accum[5] =~ m/(\d+)/);
        my ($old_c) = ($old->[5] =~ m/(\d+)/);
        if (($new_c && !test($old_c)) ||
            ($new_c > $old_c)) {
          $g_spells{$key} = \@accum;
          next;
        }
      }

      # Last resort: Save the higher spellid (BAD!)
      my $old_id = ($accum[1] =~ m/(\d+)/);
      my $new_id = ($old->[1] =~ m/(\d+)/);
      if ($new_id > $old_id) {
        $g_spells{$key} = \@accum;
      }
    }
  }
}

# Output spells and clean up.
sub cleanup() {
  # Output spells
  foreach my $k (keys(%g_spells)) {
    #print "--[$k]--" if ($k =~ /Improved Kick/);
    #print "--[$k]--" if ($k =~ /Improved Kick/);
    fprint($g_spells{$k}, $o_s_fh);
  }

  # Done, cleanup
  close($i_fh);
  close($o_s_fh) if not $dryrun;
  close($o_i_fh) if not $dryrun;
}
