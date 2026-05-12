# Dynamic Flag Generation

## Overview
This lab uses **dynamic flags** that change daily to prevent flag sharing and ensure authentic learning.

## Flag Format
All flags follow the format: `FLAG{sha1_hash}`

## How Flags Are Generated

### Flag #1 (User Access - /home/carl/flag.txt)
```bash
# Formula: SHA1(ddmmyyyy_email_ssh_bruteforce)
# Example for 05/12/2025 with carl@techvision.com:
echo -n "05122025_carl@techvision.com_ssh_bruteforce" | sha1sum
```

### Flag #2 (Root Access - /root/root_flag.txt)
```bash
# Formula: SHA1(ddmmyyyy_email_privesc_root)
# Example for 05/12/2025 with carl@techvision.com:
echo -n "05122025_carl@techvision.com_privesc_root" | sha1sum
```

## Components

### Date Component
- **Timezone**: GMT+7 (Asia/Ho_Chi_Minh)
- **Format**: ddmmyyyy (e.g., 05122025 for December 5, 2025)
- Updates automatically at midnight GMT+7

### Email Component
- **Default**: `carl@techvision.com`
- **Configurable**: Set via `EMAIL` environment variable in docker-compose.yml
- Example: `EMAIL=student@example.com`

### Suffix Component
Each flag has a unique suffix:
- Flag #1: `ssh_bruteforce`
- Flag #2: `privesc_root`

## Verifying Your Flag

To check today's flags manually:
```bash
# Get today's date in GMT+7
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Flag #1
echo -n "${GMT7_DATE}_carl@techvision.com_ssh_bruteforce" | sha1sum

# Flag #2
echo -n "${GMT7_DATE}_carl@techvision.com_privesc_root" | sha1sum
```

## Benefits

1. **Prevents Flag Sharing**: Students cannot share flags between sessions
2. **Encourages Practice**: Must complete hands-on exploitation
3. **Unique Per Day**: Each day generates new flags
4. **Customizable**: Trainers can set custom email for different cohorts

## Implementation

Flags are generated in `/entrypoint.sh` when the container starts, ensuring:
- Fresh flags for each lab session
- Correct timezone handling (GMT+7)
- Proper file permissions (600 for flags)
- Automatic service startup after flag generation
