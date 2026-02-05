import streamlit as st
import random
import time
import math

# --- INITIALIZATION ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'game_step' not in st.session_state:
    st.session_state.game_step = 'start'  # start, show_nums, guessing
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None


# --- SETTINGS ---
DIFFICULTY_RANGES = {
    'Easy': (1, 10),
    'Normal': (1, 50),
    'Hard': (1, 200),
}

TIME_LIMITS = {
    'Easy': 10,
    'Normal': 7,
    'Hard': 4,
}

SCORE_MULTIPLIER = {
    'Easy': 1,
    'Normal': 2,
    'Hard': 3,
}

OPS = {
    '+': 'add',
    '-': 'sub',
    '×': 'mul',
    '÷': 'div',
}


def get_range_for_op(op, difficulty):
    low, high = DIFFICULTY_RANGES[difficulty]
    # keep multiplication/division ranges smaller so numbers stay reasonable
    if op == '×' or op == '÷':
        return max(1, low), max(low + 5, min(high, 50))
    return low, high


def generate_question(difficulty, operations):
    if not operations:
        st.warning('Choose at least one operation in the sidebar.')
        return None

    op = random.choice(operations)
    low, high = get_range_for_op(op, difficulty)

    if op == '+':
        a = random.randint(low, high)
        b = random.randint(low, high)
        answer = a + b
        text = f"{a} + {b}"
    elif op == '-':
        a = random.randint(low, high)
        b = random.randint(low, high)
        # make subtraction usually non-negative for beginners
        if random.random() < 0.8:
            a, b = max(a, b), min(a, b)
        answer = a - b
        text = f"{a} - {b}"
    elif op == '×':
        a = random.randint(low, high)
        b = random.randint(low, high)
        answer = a * b
        text = f"{a} × {b}"
    elif op == '÷':
        # pick b not zero
        b = random.randint(low, max(low, 1))
        a = random.randint(low, high)
        # compute float division rounded to 2 decimals
        answer = round(a / b, 2)
        text = f"{a} ÷ {b} (round to 2 decimals)"
    else:
        return None

    q = {
        'text': text,
        'answer': answer,
        'op': op,
        'difficulty': difficulty,
        'time_limit': TIME_LIMITS[difficulty],
    }
    st.session_state.current_question = q
    st.session_state.game_step = 'show_nums'
    return q


# --- UI LAYOUT ---
st.title('Human Calculator')
st.sidebar.header('Game Settings')
difficulty = st.sidebar.radio('Difficulty', ['Easy', 'Normal', 'Hard'], index=1)
operations = st.sidebar.multiselect('Operations', list(OPS.keys()), default=['+'])
st.sidebar.markdown('Score multiplier: **Easy x1 • Normal x2 • Hard x3**')
st.sidebar.metric('Total Score', st.session_state.score)


# --- GAME LOGIC ---

if st.session_state.game_step == 'start':
    st.write('Welcome to Human Calculator! Choose difficulty and operations in the sidebar.')
    st.write('You must answer within the time allowed for the difficulty; points scale with difficulty.')
    if st.button('Start Game'):
        generate_question(difficulty, operations)
        st.experimental_rerun()


elif st.session_state.game_step == 'show_nums':
    q = st.session_state.current_question
    if not q:
        st.error('No question generated. Click Start Game.')
    else:
        st.subheader('Memorize the problem:')
        st.markdown(f"### {q['text']}")
        # brief display then countdown
        time.sleep(1.2)
        status = st.empty()
        for i in range(3, 0, -1):
            status.info(f'Showing for {i}...')
            time.sleep(1)
        status.empty()

        # set start time for answering
        st.session_state.start_time = time.time()
        st.session_state.game_step = 'guessing'
        st.experimental_rerun()


elif st.session_state.game_step == 'guessing':
    q = st.session_state.current_question
    if not q:
        st.error('No active question. Click Start Game.')
    else:
        time_allowed = q['time_limit']
        st.header(f'Solve: {q["text"]}')
        st.caption(f'You have {time_allowed} seconds. Difficulty: {q["difficulty"]}.')

        with st.form('math_form'):
            answer_input = st.text_input('Your answer:')
            submitted = st.form_submit_button('Submit')

            if submitted:
                elapsed = time.time() - (st.session_state.start_time or time.time())
                try:
                    # parse numeric answer
                    if isinstance(q['answer'], int):
                        user_ans = int(float(answer_input))
                    else:
                        user_ans = round(float(answer_input), 2)
                except Exception:
                    user_ans = None

                if elapsed > time_allowed:
                    st.error(f"Time's up! You took {int(elapsed)}s (limit {time_allowed}s).")
                elif user_ans is None:
                    st.error('Invalid answer format.')
                elif user_ans == q['answer']:
                    points = SCORE_MULTIPLIER[q['difficulty']]
                    st.success(f'Correct! +{points} points')
                    st.session_state.score += points
                else:
                    st.error(f'Incorrect. Correct answer: {q["answer"]}')

                # offer next round or quit
                if st.button('Next Round'):
                    generate_question(difficulty, operations)
                    st.experimental_rerun()
                if st.button('Quit'):
                    st.session_state.game_step = 'start'
                    st.session_state.current_question = None
                    st.rerun()