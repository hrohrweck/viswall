#!/usr/bin/perl

#$test="100gbit";
#$test2 = substr(lc($test), 0, index($test, "g"))."\n";

#print $test2 * 1000;


sub gbit2mbit{
        my($value)=@_;
        if(substr(lc($value),-4) != "gbit"){
                return false;
        }
        my $gbitval=substr(lc($value), 0, index($value, "g"))."\n";
        my $mbitval=$gbitval * 1000;
        print "test";
	return $mbitval."mbit";
}
my $value="1gbit";


print substr(lc($value),-4)."\n";

if(substr(lc($value),-4) ne "gbit"){
	print "test";
}
