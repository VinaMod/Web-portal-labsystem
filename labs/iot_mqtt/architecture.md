# 🏗️ Kiến Trúc Lab 4.1: The Chatty Smart Home

## 1. Mô hình triển khai (Deployment Model)

Dưới đây là sơ đồ kiến trúc của bài lab, mô tả cách các thành phần trong hệ thống Smart Home tương tác qua giao thức MQTT.

```mermaid
graph TD
    subgraph "Máy Người Dùng (Attacker Machine)"
        Attacker["User/Student<br/>(Kali Linux)"]
    end

    subgraph "Docker Lab Environment (Victim)"
        subgraph "IoT Gateway Container"
            MQTTBroker["MQTT Broker<br/>(Mosquitto)<br/>Port: 1883"]
            WebApp["Smart Home Dashboard<br/>(Flask App)<br/>Port: 8092"]
            
            subgraph "Virtual IoT Devices"
                TempSensor["Temperature Sensor<br/>(home/livingroom/temp)"]
                DoorSensor["Front Door Controller<br/>(home/frontdoor/status)"]
                SecurityHub["Security Hub Controller<br/>(home/security/door_pin)"]
            end
        end
    end

    Attacker -- "Subscribe/Eavesdrop (Port 1883)" --> MQTTBroker
    Attacker -- "HTTP Access (Port 8092)" --> WebApp
    
    SecurityHub -- "Leak UUID PIN" --> MQTTBroker
    TempSensor -- "Publish Data" --> MQTTBroker
    DoorSensor -- "Publish Status" --> MQTTBroker
```

---

## 2. Luồng khai thác (Exploitation Flow)

Sơ đồ trình tự mô tả các giai đoạn tấn công từ khi nghe trộm gói tin MQTT đến khi chiếm được Flag qua giao diện Web.

```mermaid
sequenceDiagram
    participant Attacker as Attacker (Student)
    participant MQTT as MQTT Broker (Mosquitto)
    participant Web as Web Dashboard (Flask)

    Note over Attacker, MQTT: Giai đoạn 1: Dò quét & Kết nối (Reconnaissance)
    Attacker->>MQTT: Nmap quét cổng 1883/8092
    Attacker->>MQTT: Kết nối nặc danh (Anonymous Connection)

    Note over Attacker, MQTT: Giai đoạn 2: Nghe lén (Eavesdropping)
    Attacker->>MQTT: Subscribe topic "#" (Wildcard)
    
    loop Monitoring Traffic
        MQTT-->>Attacker: home/livingroom/temp 24.5°C
        MQTT-->>Attacker: home/frontdoor/status LOCKED
        MQTT-->>Attacker: Leak PIN: {"auth_pin": "UUID-GUID", ...}
    end

    Note over Attacker, Web: Giai đoạn 3: Khai thác PIN (Exploitation)
    Attacker->>Web: Truy cập Dashboard (Port 8092)
    Attacker->>Web: Nhập mã PIN (UUID) vừa bắt được
    
    Web->>Web: Validate PIN logic
    
    alt PIN hợp lệ
        Web-->>Attacker: Unlock thành công + Trả về FLAG
    else PIN sai
        Web-->>Attacker: Access Denied
    end
```

---

## 3. Thành phần hệ thống

- **Eclipse Mosquitto**: MQTT Broker đóng vai trò trung tâm liên lạc. Cấu hình lỗi `allow_anonymous true` cho phép bất kỳ ai cũng có thể nghe trộm (Eavesdropping).
- **Virtual IoT Simulator**: Một tiến trình chạy ngầm liên tục gửi dữ liệu giả lập từ các cảm biến lên Broker, trong đó có lỗ hổng rò rỉ dữ liệu nhạy cảm (Information Disclosure).
- **Flask Web Interface**: Giao diện điều khiển Smart Home hiện đại, được bảo vệ bằng mã PIN UUID linh hoạt.
- **Dynamic Flag**: Flag được sinh ra động dựa trên Email người dùng và ngày hiện tại, đảm bảo tính duy nhất.
