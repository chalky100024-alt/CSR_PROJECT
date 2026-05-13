#!/bin/bash
export NC="\033[0m"
export RED="\033[0;31m"
export GREEN="\033[0;32m"
export YELLOW="\033[1;33m"

echo -e "${YELLOW}=== Testing rtc_alarm_set with Repeat=0 (One-Shot) vs Repeat=127 (Daily) ===${NC}"

# Current time
echo "Step 1: Sync RTC"
echo "rtc_pi2rtc" | nc -q 1 127.0.0.1 8423

# Get current RTC time to base alarm on
CURRENT_RTC=$(echo "rtc_time" | nc -q 1 127.0.0.1 8423)
echo "Current RTC Time: $CURRENT_RTC"

# Calculate target time (e.g. +5 minutes)
# Need python or complex bash date math. Let's precise ISO.
# Actually, let's just use Python for generating ISO to be safe.

TARGET_ISO=$(python3 -c "from datetime import datetime, timedelta, timezone; now = datetime.now().astimezone(); target = now + timedelta(minutes=60); print(target.isoformat(timespec='seconds'))")
echo "Target ISO (Now + 60m): $TARGET_ISO"

echo -e "\n${YELLOW}Test A: Set Alarm with Repeat=0 (Expected: Specific Date)${NC}"
CMD="rtc_alarm_set $TARGET_ISO 0"
echo "Sending: $CMD"
echo "$CMD" | nc -q 1 127.0.0.1 8423
sleep 1
echo "Checking rtc_alarm_time..."
CHECK=$(echo "rtc_alarm_time" | nc -q 1 127.0.0.1 8423)
echo "Result A: $CHECK"

echo -e "\n${YELLOW}Test B: Set Alarm with Repeat=127 (Expected: Daily? Year 2000?)${NC}"
CMD="rtc_alarm_set $TARGET_ISO 127"
echo "Sending: $CMD"
echo "$CMD" | nc -q 1 127.0.0.1 8423
sleep 1
echo "Checking rtc_alarm_time..."
CHECK=$(echo "rtc_alarm_time" | nc -q 1 127.0.0.1 8423)
echo "Result B: $CHECK"

echo -e "\n${YELLOW}Test C: Set Alarm with Repeat=0 and simplified ISO (no timezone?)${NC}"
SIMPLIFIED_ISO=${TARGET_ISO%*+*}
echo "Simplified: $SIMPLIFIED_ISO"
CMD="rtc_alarm_set $SIMPLIFIED_ISO 0"
echo "Sending: $CMD"
echo "$CMD" | nc -q 1 127.0.0.1 8423
sleep 1
echo "Checking rtc_alarm_time..."
CHECK=$(echo "rtc_alarm_time" | nc -q 1 127.0.0.1 8423)
echo "Result C: $CHECK"
