output_file="/var/log/process_metrics.log"
> $output_file
for pid in /proc/[0-9]*; do
    pid=${pid#/proc/}
    if [ -d "/proc/$pid" ]; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        cpu_stats=$(cat /proc/$pid/stat 2>/dev/null)
        mem_stats=$(cat /proc/$pid/status 2>/dev/null)
        cpu=$(echo $cpu_stats | awk '{print $14 + $15}')
        mem=$(echo "$mem_stats" | grep "VmRSS" | awk '{print $2}')
        echo "{\"pid\": \"$pid\", \"comm\": \"$comm\", \"cpu\": $cpu, \"mem\": $mem}" >> $output_file
    fi
done