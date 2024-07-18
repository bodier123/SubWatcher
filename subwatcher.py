import argparse
import asyncio
import aiohttp
import aiodns
import os
import json
from telegram import Bot
import pika

class SubWatcher:
    def __init__(self, domain, telegram_token, chat_id, use_stdout, use_telegram, use_rabbitmq, rabbitmq_url):
        self.domain = domain
        self.telegram_bot = Bot(token=telegram_token) if telegram_token else None
        self.chat_id = chat_id
        self.use_stdout = use_stdout
        self.use_telegram = use_telegram
        self.use_rabbitmq = use_rabbitmq
        self.rabbitmq_url = rabbitmq_url
        self.resolver = aiodns.DNSResolver()

    async def fetch_subdomains(self):
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return set(entry['name_value'].lower() for entry in data)

    async def resolve_domain(self, subdomain):
        try:
            result = await self.resolver.query(subdomain, 'A')
            return subdomain, [r.host for r in result]
        except aiodns.error.DNSError:
            return subdomain, None

    async def send_output(self, message):
        if self.use_stdout:
            print(message)
        
        if self.use_telegram and self.telegram_bot:
            await self.telegram_bot.send_message(chat_id=self.chat_id, text=message)
        
        if self.use_rabbitmq:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            channel.queue_declare(queue='subdomains')
            channel.basic_publish(exchange='', routing_key='subdomains', body=message)
            connection.close()

    async def check_subdomains(self):
        subdomains = await self.fetch_subdomains()
        
        known_subdomains = set()
        if os.path.exists(f"{self.domain}_subdomains.txt"):
            with open(f"{self.domain}_subdomains.txt", "r") as f:
                known_subdomains = set(line.strip() for line in f)
        
        new_subdomains = subdomains - known_subdomains
        
        if new_subdomains:
            resolve_tasks = [self.resolve_domain(subdomain) for subdomain in new_subdomains]
            resolved_subdomains = await asyncio.gather(*resolve_tasks)
            
            for subdomain, ip_addresses in resolved_subdomains:
                if ip_addresses:
                    message = json.dumps({
                        "subdomain": subdomain,
                        "ip_addresses": ip_addresses
                    })
                    await self.send_output(message)
            
            with open(f"{self.domain}_subdomains.txt", "a") as f:
                for subdomain in new_subdomains:
                    f.write(f"{subdomain}\n")
        
        return len(new_subdomains)

async def main(domain, telegram_token, chat_id, use_stdout, use_telegram, use_rabbitmq, rabbitmq_url):
    watcher = SubWatcher(domain, telegram_token, chat_id, use_stdout, use_telegram, use_rabbitmq, rabbitmq_url)
    new_subdomains_count = await watcher.check_subdomains()
    print(f"Found {new_subdomains_count} new subdomains for {domain}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor subdomains and send notifications")
    parser.add_argument("domain", help="Domain to monitor")
    parser.add_argument("--stdout", action="store_true", help="Output to stdout")
    parser.add_argument("--telegram", action="store_true", help="Send notifications via Telegram")
    parser.add_argument("--rabbitmq", action="store_true", help="Send results to RabbitMQ")
    
    args = parser.parse_args()
    
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    rabbitmq_url = os.environ.get('RABBITMQ_URL')
    
    if args.telegram and (not telegram_token or not chat_id):
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are required for Telegram output.")
        exit(1)
    
    if args.rabbitmq and not rabbitmq_url:
        print("Error: RABBITMQ_URL environment variable is required for RabbitMQ output.")
        exit(1)
    
    if not (args.stdout or args.telegram or args.rabbitmq):
        print("Error: At least one output method (--stdout, --telegram, or --rabbitmq) must be specified.")
        exit(1)
    
    asyncio.run(main(args.domain, telegram_token, chat_id, args.stdout, args.telegram, args.rabbitmq, rabbitmq_url))
