import random
import time
import math
import streamlit as st
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402 import x402ResourceServerSync
from wallet_connect import wallet_connect

FACILITATOR_URL = "https://x402.org/facilitator" 
MY_WALLET = "0xbff408b144993913af7b93406d24ad35cbb38a82"
NETWORK = "eip155:84532"  

#x402 logic
config = FacilitatorConfig(url=FACILITATOR_URL)
facilitator = HTTPFacilitatorClientSync(config)
x402_server = x402ResourceServerSync(facilitator)
x402_server.register(NETWORK, ExactEvmServerScheme())

# --- INITIALIZATION ---
if 'payment_verified' not in st.session_state:
    st.session_state.payment_verified = False
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'game_step' not in st.session_state:
    st.session_state.game_step = 'start'
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

# --- SETTINGS ---
DIFFICULTY_RANGES = {'Easy': (1, 10), 'Normal': (1, 50), 'Hard': (1, 200)}
TIME_LIMITS = {'Easy': 10, 'Normal': 7, 'Hard': 4}
SCORE_MULTIPLIER = {'Easy': 1, 'Normal': 2, 'Hard': 3}
OPS = {'+': 'add', '-': 'sub', '×': 'mul', '÷': 'div'}

def get_range_for_op(op, difficulty):
    low, high = DIFFICULTY_RANGES[difficulty]
    if op in ['×', '÷']:
        return max(1, low), max(low + 5, min(high, 50))
    return low, high

def generate_question(difficulty, operations):
    if not operations:
        st.warning('Choose at least one operation in the sidebar.')
        return None
    op = random.choice(operations)
    low, high = get_range_for_op(op, difficulty)
    if op == '+':
        a, b = random.randint(low, high), random.randint(low, high)
        answer, text = a + b, f"{a} + {b}"
    elif op == '-':
        a, b = random.randint(low, high), random.randint(low, high)
        if random.random() < 0.8: a, b = max(a, b), min(a, b)
        answer, text = a - b, f"{a} - {b}"
    elif op == '×':
        a, b = random.randint(low, high), random.randint(low, high)
        answer, text = a * b, f"{a} × {b}"
    elif op == '÷':
        b, a = random.randint(low, max(low, 1)), random.randint(low, high)
        answer, text = round(a / b, 2), f"{a} ÷ {b} (round to 2 decimals)"
    else: return None
    st.session_state.current_question = {'text': text, 'answer': answer, 'op': op, 'difficulty': difficulty, 'time_limit': TIME_LIMITS[difficulty]}
    st.session_state.game_step = 'show_nums'

# --- UI LAYOUT ---
st.title('Human Calculator')
st.sidebar.header('Game Settings')
diff = st.sidebar.radio('Difficulty', ['Easy', 'Normal', 'Hard'], index=1)
ops_selected = st.sidebar.multiselect('Operations', list(OPS.keys()), default=['+'])
st.sidebar.metric('Total Score', st.session_state.score)

# --- GAME LOGIC ---
if st.session_state.game_step == 'start':
    st.write('### 🛡️ Pay-to-Play')
    st.write('Pay **0.01 Test USDC** on Base Sepolia to unlock.')
    
    # wallet connect 
    paid = wallet_connect(
        label="Send 0.01 USDC", 
        key="pay_to_play",
        message="Enter Human Calculator Challenge",
        contract_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e", 
        amount="10000", 
        to_address=MY_WALLET 
    )

    if paid:
        st.session_state.payment_verified = True
        st.success("Payment Verified! Unlocking game...")
        time.sleep(1)
        st.rerun()

    if st.session_state.payment_verified:
        if st.button('Start Game'):
            generate_question(diff, ops_selected)
            st.rerun()

elif st.session_state.game_step == 'show_nums':
    q = st.session_state.current_question
    st.subheader('Memorize:')
    st.markdown(f"### {q['text']}")
    time.sleep(1.2)
    status = st.empty()
    for i in range(3, 0, -1):
        status.info(f'Showing for {i}...')
        time.sleep(1)
    status.empty()
    st.session_state.start_time, st.session_state.game_step = time.time(), 'guessing'
    st.rerun()

elif st.session_state.game_step == 'guessing':
    q = st.session_state.current_question
    st.header(f'Solve: {q["text"]}')
    with st.form('math_form'):
        ans_in = st.text_input('Your answer:')
        if st.form_submit_button('You sure?'):
            elapsed = time.time() - st.session_state.start_time
            try: user_ans = int(float(ans_in)) if isinstance(q['answer'], int) else round(float(ans_in), 2)
            except: user_ans = None
            if elapsed > q['time_limit']: st.error("Time's up!")
            elif user_ans == q['answer']:
                st.success("You got it dawg!")
                st.session_state.score += SCORE_MULTIPLIER[q['difficulty']]
            else: st.error(f"Mehn! Answer was {q['answer']}")
            
            # Reset triggers
            if st.button('Next Round'): generate_question(diff, ops_selected); st.rerun()
            if st.button('Quit'): st.session_state.game_step = 'start'; st.rerun()
        
