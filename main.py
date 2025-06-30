from flask import Flask, render_template, request, session, jsonify
import random
import requests
from datetime import datetime, timedelta
import os
from utils.telegram_api import send_telegram_message, add_balance

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Constants
MAIN_BOT_TOKEN = "<replace_with_main_bot_token>"
VIEW_BOT_TOKEN = "<replace_with_view_bot_token>"
ADMIN_ID = "<replace_with_admin_id>"
DAILY_SPIN_LIMIT = 15
BASE_REWARD = 2.5  # Total reward after 15 spins

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    if user_id:
        session['user_id'] = user_id
        session['spin_count'] = 0
        session['last_spin_date'] = datetime.now().strftime('%Y-%m-%d')
        session['total_earned'] = 0
        notify_admin(f"User {user_id} started game")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'})

@app.route('/spin', methods=['POST'])
def spin():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    # Check daily reset
    current_date = datetime.now().strftime('%Y-%m-%d')
    if session.get('last_spin_date') != current_date:
        session['spin_count'] = 0
        session['last_spin_date'] = current_date
        session['total_earned'] = 0
    
    # Check spin limit
    if session.get('spin_count', 0) >= DAILY_SPIN_LIMIT:
        return jsonify({'status': 'limit_reached'})
    
    # Check ad block (simplified - real implementation would be in JS)
    ad_blocked = request.json.get('ad_blocked', False)
    if ad_blocked:
        notify_admin(f"User {session['user_id']} has adblock enabled")
        return jsonify({'status': 'ad_blocked'})
    
    # Increment spin count
    session['spin_count'] = session.get('spin_count', 0) + 1
    spin_count = session['spin_count']
    
    # Calculate reward
    if spin_count < DAILY_SPIN_LIMIT:
        reward = round(random.uniform(0.1, 1.0), 2)
    else:
        reward = BASE_REWARD - session.get('total_earned', 0)
        reward = max(reward, 0.1)  # Ensure at least some reward
    
    session['total_earned'] = session.get('total_earned', 0) + reward
    
    # Prepare response
    response = {
        'status': 'success',
        'reward': reward,
        'spin_count': spin_count,
        'total_earned': session['total_earned']
    }
    
    # If last spin, add balance
    if spin_count == DAILY_SPIN_LIMIT:
        user_id = session['user_id']
        add_balance(MAIN_BOT_TOKEN, user_id, BASE_REWARD)
        notify_admin(f"User {user_id} completed 15 spins. Added ₹{BASE_REWARD}")
    
    return jsonify(response)

@app.route('/scratch', methods=['POST'])
def scratch():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    if session.get('spin_count', 0) < DAILY_SPIN_LIMIT:
        return jsonify({'status': 'error', 'message': 'Complete 15 spins first'})
    
    if session.get('scratch_used', False):
        return jsonify({'status': 'error', 'message': 'Already used scratch card'})
    
    # Generate random scratch reward
    scratch_reward = round(random.uniform(1, 5), 2)
    user_id = session['user_id']
    
    # Add balance via Telegram bot
    add_balance(MAIN_BOT_TOKEN, user_id, scratch_reward)
    session['scratch_used'] = True
    
    notify_admin(f"User {user_id} scratched and won ₹{scratch_reward}")
    
    return jsonify({
        'status': 'success',
        'reward': scratch_reward
    })

def notify_admin(message):
    send_telegram_message(VIEW_BOT_TOKEN, ADMIN_ID, message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
