# SubWatcher

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/bodier123/SubWatcher.git
   cd SubWatcher
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

SubWatcher supports multiple input methods and output options:

1. Command-line arguments:
   ```bash
   python subwatcher.py google.com facebook.com --stdout
   ```

2. File input:
   ```bash
   python subwatcher.py -f domains.txt --stdout
   ```

3. Piped input:
   ```bash
   echo "google.com" | python subwatcher.py --stdout
   ```

4. Output to file:
   ```bash
   python subwatcher.py google.com -o results.txt
   ```

You can combine these methods:
```bash
echo "google.com" | python subwatcher.py facebook.com -f more_domains.txt -o results.txt --stdout --telegram
```

### Command-line Arguments

- `domains`: Space-separated list of domains to monitor
- `-f, --file`: File containing list of domains (one per line)
- `--stdout`: Enable output to standard output
- `--telegram`: Enable Telegram notifications
- `--rabbitmq`: Enable RabbitMQ output
- `-o, --output`: Specify an output file for results

### Environment Variables

When using Telegram or RabbitMQ outputs, set the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token
- `TELEGRAM_CHAT_ID`: The chat ID to send notifications to
- `RABBITMQ_URL`: The URL of your RabbitMQ server

## Docker Support

SubWatcher can be easily run using Docker.

### Prerequisites

- Docker
- Docker Compose

### Building and Running with Docker

1. Build the Docker image:
   ```bash
   docker-compose build
   ```

2. Run SubWatcher using Docker:
   ```bash
   docker-compose run --rm subwatcher example.com --stdout
   ```
