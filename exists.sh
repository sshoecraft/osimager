#!/bin/bash
list=/tmp/list.$$
trap '{ rm -f $list; }' EXIT
bin/mkosimage -l > $list
while read spec rest
do
	path=$(bin/mkosimage vsphere/lab/$spec --dump | grep -v warning | jq '.builders[].iso_target_path' | xargs)
#	echo $spec $path
	test -f $path && echo $spec
done < $list
