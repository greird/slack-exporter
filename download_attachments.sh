#!/bin/bash 
#
# This script will browse a Slack export folder and download all files in a new /export folder
# 
# HOW TO:
# 1. As a Workspace admin, download an export of your Slack history (https://www.slack.com/services/export) 
# 2. Make sure you have jq installed (https://stedolan.github.io/jq/)
# 3. Place this file at the root of your Slack export folder, next to channels.json
# 4. Run `bash slack-files-downloader.sh -p /path/to/your/export` in your terminal
#
# OPTIONS
# -p Path to the destination folder (required)
# -o Overwrite files if they already exist in destination folder, otherwise skip them.
# -s Do not show message when a file is skipped


while getopts "osp:" flag
do
    case $flag in
        o) overwrite=true;;
        s) silent=true;;
        p) path=$OPTARG;;
    esac
done

if [ -z "$path" ]; then
    echo "Error: Destination path is required."
    echo "Usage: $0 -p <destination_path> [-o] [-s]"
    exit 1
fi

for channel in $(cat temp_slack_export/manual_export/channels.json | jq -rc '.[].name')
do
	printf "\n============================================\nLooking into #$channel...\n============================================\n"

	for file in temp_slack_export/manual_export/"$channel".json
	do
		for a in $(cat $file | jq -c '.messages[].files[0]? | [.title, .url_private_download, .filetype] | del(..|nulls)' | sed 's/ //g')
		do
			filetype=$(echo $a | jq -r '.[2]')

			if [[ $filetype == $usertype ]] || [[ -z $usertype ]] || [[ -z $filetype ]]
			then
				filename_raw=$(echo $a | jq -r '.[0]')
				
				filename=$(echo $filename_raw | sed -e 'y/āáǎàçēéěèīíǐìōóǒòūúǔùǖǘǚǜüĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛÜ/aaaaceeeeiiiioooouuuuuuuuuAAAAEEEEIIIIOOOOUUUUUUUUU/')
				filename="${filename##*/}"
				
				if [[ ! -z $filename_raw  ]] && [[ $filename_raw != "null"  ]] 
				then
					
					if [ -f "$path/$channel/$filename" ] && [[ $overwrite != true ]]
					then
						if [[ $silent != true ]]
						then
							printf "$filename already exists in destination folder. Skipping!\n"
						fi
						continue
					fi
					
					printf "Downloading $filename...\n"
						
					mkdir -p $path/$channel

					url=$(echo $a | jq -rc '.[1]')
					
					curl --progress-bar $url -o "$path/$channel/$filename"
				fi
			fi
		done
	done
done
