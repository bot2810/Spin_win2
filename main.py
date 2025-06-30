from flask import Flask, render_template, request, jsonify, session
import random
import time
import requests
import json
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'spin-and-win-secret-key-2024'

# Configuration - Replace with your actual values
MAIN_BOT_TOKEN = ""
VIEW_BOT_TOKEN = ""
ADMIN_ID = "7929115529"

# In-memory storage (replace with database for production)
user_data = {}

def get_today():
    return date.today().isoformat()

def init_user(user_id):
    today = get_today()
    if user_id not in user_data:
        user_data[user_id] = {
            'spins_today': 0,
            'daily_earnings': 0.0,
            'total_earnings': 0.0,
            'scratch_used': False,
            'last_date': today,
            'created_at': datetime.now().isoformat()
        }

    # Reset daily data if new day  
    if user_data[user_id]['last_date'] != today:
        user_data[user_id]['spins_today'] = 0
        user_data[user_id]['daily_earnings'] = 0.0
        user_data[user_id]['scratch_used'] = False
        user_data[user_id]['last_date'] = today

def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
except Exception as e:
print(f"Failed to send telegram message: {e}")
return False

def notify_admin(message):
if ADMIN_ID and VIEW_BOT_TOKEN:
send_telegram_message(VIEW_BOT_TOKEN, ADMIN_ID, message)

def add_balance_to_bot(user_id, amount):
try:
success = False

# Method 1: Direct command to main bot  
    main_bot_url = f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/sendMessage"  
      
    # Try multiple command formats for maximum compatibility  
    command_variations = [  
        f"/addbalance {user_id} {amount}",  
        f"/add {user_id} {amount}",  
        f"/balance_add {user_id} {amount}",  
        f"addbalance {user_id} {amount}",  
        f"/credit {user_id} {amount}",  
        f"/deposit {user_id} {amount}"  
    ]  
      
    for command in command_variations:  
        try:  
            # Send to admin chat first  
            admin_data = {  
                'chat_id': ADMIN_ID,  
                'text': command,  
                'parse_mode': 'HTML'  
            }  
              
            response = requests.post(main_bot_url, data=admin_data, timeout=20)  
              
            if response.status_code == 200:  
                result = response.json()  
                if result.get('ok'):  
                    print(f"✅ Command sent successfully: {command} to {ADMIN_ID}")  
                    success = True  
                    break  
                else:  
                    print(f"❌ Telegram API error: {result}")  
            else:  
                print(f"❌ HTTP error {response.status_code} for command: {command}")  
              
            # Small delay between attempts  
            time.sleep(0.5)  
              
        except Exception as cmd_error:  
            print(f"❌ Error with command {command}: {cmd_error}")  
            continue  
      
    # Method 2: If direct command fails, try webhook approach  
    if not success:  
        try:  
            webhook_data = {  
                'chat_id': ADMIN_ID,  
                'text': f"🚀 INSTANT BALANCE ADD REQUEST\n\n💰 Amount: ₹{amount}\n👤 User ID: {user_id}\n⚡ Execute: /addbalance {user_id} {amount}\n\n⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",  
                'parse_mode': 'HTML',  
                'reply_markup': json.dumps({  
                    'inline_keyboard': [[  
                        {  
                            'text': f'✅ Add ₹{amount}',  
                            'callback_data': f'add_balance_{user_id}_{amount}'  
                        }  
                    ]]  
                })  
            }  
              
            webhook_response = requests.post(main_bot_url, data=webhook_data, timeout=15)  
              
            if webhook_response.status_code == 200:  
                webhook_result = webhook_response.json()  
                if webhook_result.get('ok'):  
                    print(f"✅ Webhook method successful for user {user_id}")  
                    success = True  
                else:  
                    print(f"❌ Webhook error: {webhook_result}")  
            else:  
                print(f"❌ Webhook HTTP error: {webhook_response.status_code}")  
                  
        except Exception as webhook_error:  
            print(f"❌ Webhook method failed: {webhook_error}")  
      
    # Method 3: Multiple rapid-fire commands for maximum impact  
    if not success:  
        try:  
            rapid_commands = [  
                f"/addbalance {user_id} {amount}",  
                f"/addbalance {user_id} {amount}",  
                f"/add {user_id} {amount}"  
            ]  
              
            for rapid_cmd in rapid_commands:  
                rapid_data = {  
                    'chat_id': ADMIN_ID,  
                    'text': rapid_cmd,  
                    'parse_mode': 'HTML'  
                }  
                  
                rapid_response = requests.post(main_bot_url, data=rapid_data, timeout=10)  
                  
                if rapid_response.status_code == 200:  
                    rapid_result = rapid_response.json()  
                    if rapid_result.get('ok'):  
                        print(f"✅ Rapid command successful: {rapid_cmd}")  
                        success = True  
                        break  
                  
                time.sleep(0.2)  # Very short delay  
                  
        except Exception as rapid_error:  
            print(f"❌ Rapid method failed: {rapid_error}")  
      
    # Method 4: Fallback notification via view bot  
    if not success:  
        try:  
            view_bot_url = f"https://api.telegram.org/bot{VIEW_BOT_TOKEN}/sendMessage"  
            fallback_data = {  
                'chat_id': ADMIN_ID,  
                'text': f"🚨 URGENT BALANCE REQUEST\n\n💰 Add ₹{amount} to User: {user_id}\n⚡ Command: /addbalance {user_id} {amount}\n\n🔄 Auto-retry failed - Manual action required!",  
                'parse_mode': 'HTML'  
            }  
              
            fallback_response = requests.post(view_bot_url, data=fallback_data, timeout=10)  
              
            if fallback_response.status_code == 200:  
                fallback_result = fallback_response.json()  
                success = fallback_result.get('ok', False)  
                print(f"✅ Fallback notification sent successfully")  
            else:  
                print(f"❌ Fallback notification failed: {fallback_response.status_code}")  
                  
        except Exception as fallback_error:  
            print(f"❌ Fallback method failed: {fallback_error}")  
      
    return success  
      
except Exception as e:  
    print(f"❌ Critical error in add_balance_to_bot: {e}")  
    # Emergency notification  
    try:  
        emergency_url = f"https://api.telegram.org/bot{VIEW_BOT_TOKEN}/sendMessage"  
        emergency_data = {  
            'chat_id': ADMIN_ID,  
            'text': f"🆘 EMERGENCY: Balance add system failure!\n\nUser: {user_id}\nAmount: ₹{amount}\nError: {str(e)}\n\n⚠️ MANUAL INTERVENTION REQUIRED!",  
            'parse_mode': 'HTML'  
        }  
        requests.post(emergency_url, data=emergency_data, timeout=5)  
    except:  
        pass  
      
    return False

@app.route('/')
def index():
return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
data = request.get_json()
user_id = data.get('user_id', '').strip()

if not user_id or not user_id.isdigit() or len(user_id) < 5:  
    return jsonify({'success': False, 'message': 'Invalid Telegram User ID'})  

session['user_id'] = user_id  
init_user(user_id)  

# Notify admin about user entry  
notify_admin(f"🚪 User {user_id} entered the site")  
notify_admin(f"🆕 User {user_id} started using the game")  

return jsonify({'success': True})

@app.route('/game-data')
def game_data():
if 'user_id' not in session:
return jsonify({'error': 'Not logged in'})

user_id = session['user_id']  
init_user(user_id)  
data = user_data[user_id]  

return jsonify({  
    'user_id': user_id,  
    'spins_today': data['spins_today'],  
    'daily_earnings': data['daily_earnings'],  
    'total_earnings': data['total_earnings'],  
    'scratch_used': data['scratch_used'],  
    'spins_remaining': 15 - data['spins_today']  
})

@app.route('/spin', methods=['POST'])
def spin():
if 'user_id' not in session:
return jsonify({'success': False, 'message': 'Not logged in'})

data = request.get_json()  
ad_viewed = data.get('ad_viewed', False)  

if not ad_viewed:  
    return jsonify({'success': False, 'message': 'Please view the ad first!'})  

user_id = session['user_id']  
init_user(user_id)  
user = user_data[user_id]  

if user['spins_today'] >= 15:  
    return jsonify({'success': False, 'message': 'Daily spin limit reached!'})  

# Generate reward  
rewards = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.80, 1.00]  
visual_reward = random.choice(rewards)  

# Calculate actual earning to reach ₹2.50 total  
target_total = 2.50  
spins_left = 15 - user['spins_today']  
remaining_amount = target_total - user['daily_earnings']  

if spins_left == 1:  
    actual_reward = max(0.10, remaining_amount)  
else:  
    actual_reward = min(visual_reward, remaining_amount / spins_left * random.uniform(0.8, 1.5))  

actual_reward = round(actual_reward, 2)  

# Update user data  
user['spins_today'] += 1  
user['daily_earnings'] += actual_reward  
user['total_earnings'] += actual_reward  

# Determine spin result (emoji zones)  
zones = ['😘', '🥰', '🥳']  
winning_zone = random.choice(zones)  

result = {  
    'success': True,  
    'visual_reward': visual_reward,  
    'actual_reward': actual_reward,  
    'winning_zone': winning_zone,  
    'spins_remaining': 15 - user['spins_today'],  
    'daily_earnings': user['daily_earnings'],  
    'show_scratch': user['spins_today'] == 15 and not user['scratch_used']  
}  

# Don't notify admin for every spin - only on entry and scratch  

return jsonify(result)

@app.route('/scratch', methods=['POST'])
def scratch():
if 'user_id' not in session:
return jsonify({'success': False, 'message': 'Not logged in'})

user_id = session['user_id']  
init_user(user_id)  
user = user_data[user_id]  

if user['spins_today'] < 15:  
    return jsonify({'success': False, 'message': 'Complete 15 spins first!'})  

if user['scratch_used']:  
    return jsonify({'success': False, 'message': 'Scratch card already used today!'})  

# Show fixed ₹2.50 in scratch card (same as daily earnings)  
scratch_reward = 2.50  

# Update user data  
user['scratch_used'] = True  
# Don't add extra money, just show the same ₹2.50  

# Send money to main bot AFTER scratch  
balance_sent = add_balance_to_bot(user_id, 2.50)  

# Notify admin about scratch  
notify_admin(f"🎫 User {user_id} used scratch card\n💰 Revealed: ₹{scratch_reward}")  

# Notify admin about money sent to main bot  
if balance_sent:  
    notify_admin(f"✅ Successfully sent ₹2.50 to user {user_id}")  
else:  
    notify_admin(f"❌ FAILED to send ₹2.50 to user {user_id} - Manual action required!")  
      
# Try alternative method if first attempt failed  
if not balance_sent:  
    # Retry with different approach  
    time.sleep(2)  
    retry_success = add_balance_to_bot(user_id, 2.50)  
    if retry_success:  
        notify_admin(f"✅ Retry successful - sent ₹2.50 to user {user_id}")  
    else:  
        notify_admin(f"🚨 URGENT: Manual balance addition needed for user {user_id} - Amount: ₹2.50")  

return jsonify({  
    'success': True,  
    'reward': scratch_reward,  
    'total_earnings': user['total_earnings']  
})

@app.route('/logout', methods=['POST'])
def logout():
session.clear()
return jsonify({'success': True})

@app.route('/track-ad-click', methods=['POST'])
def track_ad_click():
# Ad click tracking endpoint
data = request.get_json()
position = data.get('position', 'unknown')
timestamp = data.get('timestamp', '')

# Log ad click (in production, you might want to store this in database)  
print(f"Ad clicked: {position} at {timestamp}")  
  
return jsonify({'success': True})

if name == 'main':
import os
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=False)
