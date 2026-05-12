# Dynamic Flag Generation

## Overview
This lab uses **dynamic flags** that change daily to ensure authentic learning and preventing flag sharing.

## Lab Management

### Quick Commands

**Start/Build Lab (Default):**
```bash
docker compose up -d --build
```

**Start with Custom Email:**
```bash
# Replace 'student@university.edu' with your desired email
EMAIL=student@university.edu docker compose up -d --build
```

**Stop Lab:**
```bash
docker compose down
```

**View Logs (Debugging):**
```bash
docker compose logs -f
```

## Flag Format
All flags follow the format: `FLAG{sha1_hash}`

## How Flags Are Generated

### Flag #1 (Race Condition Exploit)
The flag is displayed in the Modal after successfully exploiting the Race Condition vulnerability to reduce the price to 0₫.

```bash
# Formula: SHA1(ddmmyyyy_email_race_condition_2)
# Example for 12/01/2026 with carl@techvision.com:
echo -n "12012026_carl@techvision.com_race_condition_2" | sha1sum
```

## Components

### Date Component
- **Timezone**: GMT+7 (Asia/Ho_Chi_Minh)
- **Format**: ddmmyyyy (e.g., 12012026 for January 12, 2026)
- Updates automatically at midnight GMT+7

### Email Component
- **Default**: `carl@techvision.com`
- **Configurable**: Set via `EMAIL` environment variable in `docker-compose.yml` for the `web` service.

### Suffix Component
- Fixed suffix: `race_condition_2`

## Verifying Your Flag

To check today's flag manually on a Linux/Mac terminal:
```bash
# Get today's date in GMT+7
GMT7_DATE=$(TZ=Asia/Ho_Chi_Minh date +%d%m%Y)

# Generate Hash
echo -n "${GMT7_DATE}_carl@techvision.com_race_condition_2" | sha1sum
```
