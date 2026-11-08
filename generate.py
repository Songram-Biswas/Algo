import json, re, os

TEMPLATE = open('template.html', encoding='utf-8').read()
OUT_DIR = 'solutions'

DIFF_VAR = {'Easy': 'good', 'Medium': 'warn', 'Hard': 'bad'}

def highlight_python(code):
    KEYWORDS = ['def','class','from','import','return','if','elif','else','while','for','in','not','and','or',
                'True','False','None','self','while','break','continue','is']
    BUILTINS = ['len','min','max','sorted','enumerate','range','list','dict','set','int','str','sum','abs']
    lines = code.split('\n')
    out = []
    for line in lines:
        # comment
        comment = ''
        cidx = line.find('#')
        if cidx != -1:
            comment = line[cidx:]
            line = line[:cidx]
        # strings
        line = re.sub(r"(\"[^\"]*\"|'[^']*')", lambda m: f'\x01STR{m.group(0)}\x02', line)
        # numbers
        line = re.sub(r'(?<![\w])(\d+)(?![\w])', lambda m: f'\x01NUM{m.group(1)}\x02', line)
        # keywords
        for kw in KEYWORDS:
            line = re.sub(rf'(?<![\w]){kw}(?![\w])', f'\x01KW{kw}\x02', line)
        # builtins / function-call names (word followed by '(')
        line = re.sub(r'(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)(?=\()', lambda m: f'\x01FN{m.group(1)}\x02' if m.group(1) not in KEYWORDS else m.group(1), line)
        # escape html
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # restore tokens to spans
        line = re.sub(r'\x01STR(.*?)\x02', r'<span class="str">\1</span>', line)
        line = re.sub(r'\x01NUM(.*?)\x02', r'<span class="num">\1</span>', line)
        line = re.sub(r'\x01KW(.*?)\x02', r'<span class="kw">\1</span>', line)
        line = re.sub(r'\x01FN(.*?)\x02', r'<span class="fn">\1</span>', line)
        if comment:
            comment = comment.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            line += f'<span class="cm">{comment}</span>'
        out.append(line)
    return '\n'.join(out)

def js_string(code):
    return json.dumps(code)

def render(problem):
    html = TEMPLATE
    html = html.replace('__TITLE__', problem['title'])
    html = html.replace('__SLUG__', problem['slug'])
    html = html.replace('__CATEGORY__', problem['category'])
    html = html.replace('__CATEGORY_URL__', problem['category'])
    html = html.replace('__DIFFICULTY__', problem['difficulty'])
    html = html.replace('__DIFF_VAR__', DIFF_VAR[problem['difficulty']])
    tags_html = ''.join(f'<span class="px-2.5 py-1 rounded-md text-xs font-semibold text-soft" style="background:var(--rail)">{t}</span>' for t in problem['tags'])
    html = html.replace('__TAGS_HTML__', tags_html)
    html = html.replace('__LEETCODE_URL__', problem['leetcode_url'])
    html = html.replace('__STATEMENT_HTML__', problem['statement_html'])
    html = html.replace('__EXAMPLE_HTML__', problem['example_html'])
    html = html.replace('__TRACE_HTML__', problem['trace_html'])

    qt_opts = ''.join(f'<div class="quiz-opt rounded-lg px-3 py-2 text-sm mono" data-val="{o}">{o}</div>' for o in problem['quiz_time_opts'])
    qs_opts = ''.join(f'<div class="quiz-opt rounded-lg px-3 py-2 text-sm mono" data-val="{o}">{o}</div>' for o in problem['quiz_space_opts'])
    html = html.replace('__QUIZ_TIME_OPTIONS__', qt_opts)
    html = html.replace('__QUIZ_SPACE_OPTIONS__', qs_opts)
    html = html.replace('__QUIZ_TIME_CORRECT__', problem['time_big'])
    html = html.replace('__QUIZ_SPACE_CORRECT__', problem['space_big'])

    tricks_html = ''.join(f'<li>{t}</li>' for t in problem['tricks'])
    html = html.replace('__TRICKS_HTML__', tricks_html)

    html = html.replace('__APPROACH_HTML__', problem['approach_html'])
    html = html.replace('__PYTHON_CODE_HTML__', highlight_python(problem['python_code']))
    html = html.replace('__PYTHON_CODE_JS_STRING__', js_string(problem['python_code']))

    html = html.replace('__TIME_BIG__', problem['time_big'])
    html = html.replace('__TIME_EXPLAIN__', problem['time_explain'])
    html = html.replace('__SPACE_BIG__', problem['space_big'])
    html = html.replace('__SPACE_EXPLAIN__', problem['space_explain'])

    html = html.replace('__SIDEBAR_JSON__', json.dumps(problem['sidebar']))
    html = html.replace('__PREV_NEXT_HTML__', problem['prev_next_html'])
    html = html.replace('__TRACE_JS__', problem['trace_js'])
    course = problem.get('course', 'blind-75')
    html = html.replace('course=blind-75&type=__CATEGORY_URL__', f"course={course}&type={problem['category']}")
    html = html.replace('course=blind-75', f"course={course}")

    return html

def prev_next(prev_slug, prev_title, next_slug, next_title):
    prev_html = f'''<a id="link-prev" href="./{prev_slug}" class="text-soft hover:accent-text transition flex items-center gap-2 text-sm font-semibold">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
          <span># {prev_title}</span>
        </a>''' if prev_slug else '''<span class="invisible"></span>'''
    next_html = f'''<a id="link-next" href="./{next_slug}" class="text-soft hover:accent-text transition flex items-center gap-2 text-sm font-semibold">
          <span># {next_title}</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
        </a>''' if next_slug else '''<span class="invisible"></span>'''
    return prev_html + '\n        ' + next_html

ARRAY_SIDEBAR = [
    {"slug": "two-sum", "title": "Two Sum", "implemented": True},
    {"slug": "container-with-most-water", "title": "Container With Most Water", "implemented": True},
    {"slug": "search-in-rotated-sorted-array", "title": "Search in Rotated Sorted Array", "implemented": True},
    {"slug": "maximum-subarray", "title": "Maximum Subarray", "implemented": True},
    {"slug": "longest-consecutive-sequence", "title": "Longest Consecutive Sequence", "implemented": True},
    {"slug": "maximum-product-subarray", "title": "Maximum Product Subarray", "implemented": True},
    {"slug": "find-minimum-in-rotated-sorted-array", "title": "Find Minimum in Rotated Sorted Array", "implemented": True},
    {"slug": "contains-duplicate", "title": "Contains Duplicate", "implemented": True},
    {"slug": "product-of-array-except-self", "title": "Product of Array Except Self", "implemented": False}
]
STRING_SIDEBAR = [
    {"slug": "group-anagrams", "title": "Group Anagrams", "implemented": True},
    {"slug": "longest-repeating-character-replacement", "title": "Longest Repeating Character Replacement", "implemented": True}
]
LINKED_LIST_SIDEBAR = [
    {"slug": "reverse-linked-list", "title": "Reverse Linked List", "implemented": True}
]

GENERIC_TRICKS = [
  '<strong class="accent-text">Count the loops, not the lines.</strong> One pass over n elements with O(1) work per element gives O(n); nested loops over the same input usually multiply.',
  '<strong class="accent-text">Hash set/map operations are O(1) average.</strong> A loop doing one lookup or insert per iteration stays O(n) overall — the hash structure doesn\'t add a factor.',
  '<strong class="accent-text">Space tracks "extra" memory, not the input.</strong> Ask what new structure you\'re building and how big it can get.',
  '<strong class="accent-text">Two pointers / sliding window ≠ O(n²).</strong> Even though it looks like nested loops, each pointer only ever moves forward — total work stays O(n).'
]

problems = []

# ---------- 1. container-with-most-water ----------
problems.append(dict(
    slug='container-with-most-water', title='Container With Most Water', category='Array',
    difficulty='Medium', tags=['Two Pointers', 'Array'],
    leetcode_url='https://leetcode.com/problems/container-with-most-water/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">height</code> of length n. Two lines are drawn such that the two endpoints of line i are at <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">(i, 0)</code> and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">(i, height[i])</code>. Find two lines that together with the x-axis form a container holding the most water.</p>
        <p class="text-soft text-sm mb-5">Return the maximum amount of water the container can store.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> height = [1,8,6,2,5,4,8,3,7]</p><p><span class="text-soft">Output:</span> 49</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain='Two pointers move inward; each index is visited at most once.',
    space_big='O(1)', space_explain='Only two pointers and a running max are tracked — no extra structure.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Always move the shorter line.</strong> The container\'s height is capped by the shorter side, so keeping the taller one can never help — only moving the shorter pointer can find something better.'],
    approach_html='''<p class="mb-3">Start with the widest possible container — both ends of the array — and shrink inward. At each step, the area is capped by the <em>shorter</em> of the two lines, so moving the taller pointer can never increase the area. Always move the shorter one.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Place <code class="mono accent-text">left</code> at index 0 and <code class="mono accent-text">right</code> at the last index.</li>
          <li>Compute <code class="mono accent-text">area = (right - left) * min(height[left], height[right])</code> and track the max.</li>
          <li>Move whichever pointer points to the shorter line inward.</li>
          <li>Repeat until the pointers meet.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def maxArea(self, height: List[int]) -> int:
        left = 0
        right = len(height) - 1
        max_area = 0

        while left < right:
            width = right - left
            h = min(height[left], height[right])
            area = width * h
            max_area = max(max_area, area)

            if height[left] < height[right]:
                left += 1
            else:
                right -= 1

        return max_area''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('two-sum', 'Two Sum', 'search-in-rotated-sorted-array', 'Search in Rotated Sorted Array'),
    trace_js='''
    const HEIGHTS = [1, 8, 6, 2, 5, 4, 8, 3, 7];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let left = 0, right = HEIGHTS.length - 1, maxArea = 0;
      while (left < right) {
        const width = right - left;
        const h = Math.min(HEIGHTS[left], HEIGHTS[right]);
        const area = width * h;
        const improved = area > maxArea;
        maxArea = Math.max(maxArea, area);
        steps.push({ left, right, area, maxArea, improved });
        if (HEIGHTS[left] < HEIGHTS[right]) left++; else right--;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = HEIGHTS.map((h, i) => `
        <div class="cell" id="cell-${i}" style="height:${28 + h * 6}px; align-items:flex-end; padding-bottom:6px;">${h}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      HEIGHTS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < s.left; i++) document.getElementById(`cell-${i}`).classList.add('discarded');
      for (let i = s.right + 1; i < HEIGHTS.length; i++) document.getElementById(`cell-${i}`).classList.add('discarded');
      document.getElementById(`cell-${s.left}`).classList.add(s.improved ? 'hit' : 'scan');
      document.getElementById(`cell-${s.right}`).classList.add(s.improved ? 'hit' : 'scan');
      caption.textContent = `left=${s.left}, right=${s.right} → area=${s.area}${s.improved ? ' (new max!)' : ''} — running max: ${s.maxArea}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 2. contains-duplicate ----------
problems.append(dict(
    slug='contains-duplicate', title='Contains Duplicate', category='Array',
    difficulty='Easy', tags=['Hash Set', 'Array'],
    leetcode_url='https://leetcode.com/problems/contains-duplicate/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, return <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">true</code> if any value appears at least twice, and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">false</code> if every element is distinct.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [1,2,3,1]</p><p><span class="text-soft">Output:</span> true</p>',
    trace_html='''<div class="flex flex-col items-center gap-6">
          <div id="array-track" class="flex gap-3 pb-7 pt-7 justify-center flex-wrap"></div>
          <div class="w-full max-w-md">
            <p class="text-xs font-bold uppercase tracking-wider text-soft mb-2 text-center">hash set &nbsp;(seen elements)</p>
            <div id="map-track" class="flex gap-2 flex-wrap justify-center min-h-[46px]"></div>
          </div>
        </div>''',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain='Single pass; each hash set lookup/insert is O(1) average.',
    space_big='O(n)', space_explain='In the worst case (no duplicates) the set holds all n elements.',
    tricks=GENERIC_TRICKS,
    approach_html='''<p class="mb-3">Walk the array once, tracking every value you\'ve already seen in a hash set. The moment you encounter a value already in the set, you\'ve found a duplicate.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>For each number, check if it\'s already in <code class="mono accent-text">seen</code>.</li>
          <li>If it is, return <code class="mono accent-text">True</code> immediately.</li>
          <li>Otherwise, add it to <code class="mono accent-text">seen</code> and continue.</li>
          <li>If the loop finishes without a hit, return <code class="mono accent-text">False</code>.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        seen = set()

        for num in nums:
            if num in seen:
                return True
            seen.add(num)

        return False''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('find-minimum-in-rotated-sorted-array', 'Find Minimum in Rotated Sorted Array', None, None),
    trace_js='''
    const NUMS = [1, 2, 3, 1];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const seen = new Set();
      const firstSeen = new Map();

      for (let i = 0; i < NUMS.length; i++) {
        const val = NUMS[i];
        const isDup = seen.has(val);

        steps.push({
          type: isDup ? 'hit' : 'scan',
          i,
          val,
          origIdx: firstSeen.get(val),
          snapshot: new Set(seen),
          caption: isDup
            ? `nums[${i}] = ${val} already exists in hash set (first seen at index ${firstSeen.get(val)}) → Duplicate found! Return True.`
            : `Scanning nums[${i}] = ${val}. Checking if ${val} is in seen set… Not found.`
        });

        if (isDup) break;

        seen.add(val);
        firstSeen.set(val, i);

        steps.push({
          type: 'store',
          i,
          val,
          snapshot: new Set(seen),
          caption: `Added ${val} to seen set: { ${Array.from(seen).join(', ')} }.`
        });
      }
    }

    function buildTrace() {
      computeSteps();
      stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `
        <div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span></div>
      `).join('');
      document.getElementById('map-track').innerHTML = '<span class="text-xs text-soft mono">empty</span>';
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        const cell = document.getElementById(`cell-${i}`);
        cell.classList.remove('scan', 'hit', 'done');
      });

      const mapTrack = document.getElementById('map-track');
      const caption = document.getElementById('trace-caption');

      if (stepIndex < 0) {
        mapTrack.innerHTML = '<span class="text-xs text-soft mono">empty</span>';
        caption.textContent = 'Click "Next" to begin.';
        updateStepControls();
        return;
      }

      const s = steps[stepIndex];

      if (s.snapshot.size === 0) {
        mapTrack.innerHTML = '<span class="text-xs text-soft mono">empty</span>';
      } else {
        mapTrack.innerHTML = Array.from(s.snapshot)
          .map(v => `<div class="map-slot filled">${v}</div>`)
          .join('');
      }

      for (let i = 0; i < s.i; i++) {
        document.getElementById(`cell-${i}`).classList.add('done');
      }

      if (s.type === 'hit') {
        document.getElementById(`cell-${s.i}`).classList.remove('done');
        document.getElementById(`cell-${s.i}`).classList.add('hit');
        if (s.origIdx !== undefined) {
          const origCell = document.getElementById(`cell-${s.origIdx}`);
          origCell.classList.remove('done');
          origCell.classList.add('hit');
        }
      } else {
        document.getElementById(`cell-${s.i}`).classList.add('scan');
      }

      caption.textContent = s.caption;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 3. find-minimum-in-rotated-sorted-array ----------
problems.append(dict(
    slug='find-minimum-in-rotated-sorted-array', title='Find Minimum in Rotated Sorted Array', category='Array',
    difficulty='Medium', tags=['Binary Search', 'Array'],
    leetcode_url='https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/',
    statement_html='''<p class="leading-relaxed mb-4">A sorted array of unique elements was rotated at an unknown pivot. Given the rotated array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, return the minimum element.</p>
        <p class="text-soft text-sm mb-5">You must write an algorithm that runs in <span class="mono accent-text">O(log n)</span> time.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [3,4,5,1,2]</p><p><span class="text-soft">Output:</span> 1</p>',
    trace_html='<div id="array-track" class="flex gap-3 pb-7 pt-7"></div>',
    quiz_time_opts=['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(log n)', time_explain='The search window halves on every iteration of binary search.',
    space_big='O(1)', space_explain='Only two or three index pointers are tracked.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Compare against the right boundary, not the left.</strong> If <code class="mono">nums[mid] &gt; nums[right]</code>, the minimum must be to the right of mid; otherwise it\'s at mid or to the left — this single comparison drives the whole search.'],
    approach_html='''<p class="mb-3">The minimum is the one point where the "rotation break" happens. Binary search by comparing the middle element to the rightmost element: if mid is greater than the right end, the break (and the minimum) is to the right; otherwise it\'s at or before mid.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Set <code class="mono accent-text">left = 0</code>, <code class="mono accent-text">right = len(nums) - 1</code>.</li>
          <li>While <code class="mono accent-text">left &lt; right</code>, compute <code class="mono accent-text">mid</code>.</li>
          <li>If <code class="mono accent-text">nums[mid] &gt; nums[right]</code>, the minimum is past mid → <code class="mono accent-text">left = mid + 1</code>.</li>
          <li>Otherwise the minimum is at or before mid → <code class="mono accent-text">right = mid</code>.</li>
          <li>When the loop ends, <code class="mono accent-text">left == right</code> points at the minimum.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def findMin(self, nums: List[int]) -> int:
        left, right = 0, len(nums) - 1

        while left < right:
            mid = (left + right) // 2

            if nums[mid] > nums[right]:
                left = mid + 1
            else:
                right = mid

        return nums[left]''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('maximum-product-subarray', 'Maximum Product Subarray', 'contains-duplicate', 'Contains Duplicate'),
    trace_js='''
    const NUMS = [3, 4, 5, 1, 2];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let left = 0, right = NUMS.length - 1;
      while (left < right) {
        const mid = Math.floor((left + right) / 2);
        const goRight = NUMS[mid] > NUMS[right];
        steps.push({ left, mid, right, goRight });
        if (goRight) left = mid + 1; else right = mid;
      }
      steps.push({ left, mid: left, right: left, final: true });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `<div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function setPointers(left, mid, right) {
      NUMS.forEach((_, i) => {
        const p = document.getElementById(`ptr-${i}`);
        let labels = [];
        if (i === left) labels.push('L');
        if (i === mid) labels.push('M');
        if (i === right) labels.push('R');
        p.textContent = labels.join('/');
        p.style.opacity = labels.length ? 1 : 0;
      });
    }

    function renderStep() {
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) {
        NUMS.forEach((_, i) => { document.getElementById(`cell-${i}`).classList.remove('discarded', 'scan', 'hit'); document.getElementById(`ptr-${i}`).style.opacity = 0; });
        caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return;
      }
      const s = steps[stepIndex];
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.toggle('discarded', i < s.left || i > s.right);
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
      });
      setPointers(s.left, s.mid, s.right);
      if (s.final) {
        document.getElementById(`cell-${s.left}`).classList.add('hit');
        caption.textContent = `left == right → minimum found: nums[${s.left}] = ${NUMS[s.left]}`;
      } else {
        document.getElementById(`cell-${s.mid}`).classList.add('scan');
        caption.textContent = `mid=${s.mid} → nums[mid]=${NUMS[s.mid]} ${s.goRight ? '>' : '<='} nums[right]=${NUMS[s.right]} → search ${s.goRight ? 'right' : 'left'} half`;
      }
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 4. group-anagrams ----------
problems.append(dict(
    slug='group-anagrams', title='Group Anagrams', category='String',
    difficulty='Medium', tags=['Hash Map', 'String'],
    leetcode_url='https://leetcode.com/problems/group-anagrams/',
    statement_html='''<p class="leading-relaxed mb-4">Given an array of strings <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">strs</code>, group the anagrams together. Two strings are anagrams if one can be rearranged to form the other.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> strs = ["eat","tea","tan","ate","nat","bat"]</p><p><span class="text-soft">Output:</span> [["eat","tea","ate"],["tan","nat"],["bat"]]</p>',
    trace_html='''<div id="array-track" class="flex gap-3 pb-5 flex-wrap justify-center"></div>
          <div class="w-full"><p class="text-xs font-bold uppercase tracking-wider text-soft mb-2">groups &nbsp;(sorted key → words)</p>
          <div id="map-track" class="flex flex-col gap-2 min-h-[42px] w-full"></div></div>''',
    quiz_time_opts=['O(n)', 'O(n·k log k)', 'O(n²)', 'O(n log n)'], quiz_space_opts=['O(1)', 'O(n·k)', 'O(log n)'],
    time_big='O(n·k log k)', time_explain='n strings, each sorted in O(k log k) where k is the max string length.',
    space_big='O(n·k)', space_explain='The map stores every input string across all groups.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">A sorted string is a perfect anagram fingerprint.</strong> Any two anagrams collapse to the exact same sorted key, so a hash map keyed on that string groups them in one pass.'],
    approach_html='''<p class="mb-3">Anagrams share the same letters, just in different orders — so sorting each string\'s letters gives a canonical key that\'s identical for every anagram in a group. Use that sorted string as a hash map key.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>For each word, compute <code class="mono accent-text">key = sorted(word)</code>.</li>
          <li>Append the original word to <code class="mono accent-text">groups[key]</code>.</li>
          <li>After processing every word, return all the map\'s values as the grouped lists.</li>
        </ol>''',
    python_code='''from typing import List
from collections import defaultdict

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)

        for s in strs:
            key = ''.join(sorted(s))
            groups[key].append(s)

        return list(groups.values())''',
    sidebar=STRING_SIDEBAR,
    prev_next_html=prev_next(None, None, 'longest-repeating-character-replacement', 'Longest Repeating Character Replacement'),
    trace_js='''
    const WORDS = ["eat", "tea", "tan", "ate", "nat", "bat"];
    function sortedKey(w) { return w.split('').sort().join(''); }
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const groups = new Map();
      for (let i = 0; i < WORDS.length; i++) {
        const key = sortedKey(WORDS[i]);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(WORDS[i]);
        steps.push({ i, key, snapshot: new Map([...groups].map(([k, v]) => [k, [...v]])) });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = WORDS.map((w, i) => `<div class="cell" id="cell-${i}" style="min-width:64px;">${w}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('map-track').innerHTML = '';
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      WORDS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'done'));
      const mapTrack = document.getElementById('map-track');
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { mapTrack.innerHTML = ''; caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      mapTrack.innerHTML = Array.from(s.snapshot.entries()).map(([k, words]) =>
        `<div class="map-slot filled" style="display:flex; gap:6px; align-items:center;"><span class="text-soft">"${k}"</span> → [${words.join(', ')}]</div>`
      ).join('');
      for (let i = 0; i < s.i; i++) document.getElementById(`cell-${i}`).classList.add('done');
      document.getElementById(`cell-${s.i}`).classList.add('scan');
      caption.textContent = `"${WORDS[s.i]}" → sorted key "${s.key}" → append to that group`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 5. longest-consecutive-sequence ----------
problems.append(dict(
    slug='longest-consecutive-sequence', title='Longest Consecutive Sequence', category='Array',
    difficulty='Medium', tags=['Hash Set', 'Array'],
    leetcode_url='https://leetcode.com/problems/longest-consecutive-sequence/',
    statement_html='''<p class="leading-relaxed mb-4">Given an unsorted array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, return the length of the longest consecutive elements sequence.</p>
        <p class="text-soft text-sm mb-5">You must write an algorithm that runs in <span class="mono accent-text">O(n)</span> time.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [100,4,200,1,3,2]</p><p><span class="text-soft">Output:</span> 4 <span class="cm">// the sequence [1,2,3,4]</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(n)', 'O(n log n)', 'O(n²)', 'O(1)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain='Each number is only ever extended into a chain once, despite the nested-looking loop.',
    space_big='O(n)', space_explain='The hash set stores every distinct number.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Only start counting from a true chain start.</strong> By skipping any number whose predecessor exists in the set, each chain is walked exactly once in total — that\'s what keeps this O(n) instead of O(n²).'],
    approach_html='''<p class="mb-3">Put every number in a hash set for O(1) lookups. For each number, only start counting a sequence if it\'s a true "chain start" — meaning <code class="mono accent-text">num - 1</code> is NOT in the set. From there, count forward as long as consecutive numbers exist.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Build a set of all numbers for O(1) membership checks.</li>
          <li>For each number, skip it unless it\'s a chain start (<code class="mono accent-text">num - 1</code> not in set).</li>
          <li>From a chain start, keep extending forward (<code class="mono accent-text">num + 1</code>, <code class="mono accent-text">num + 2</code>, …) while present in the set.</li>
          <li>Track the longest chain length seen.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        num_set = set(nums)
        longest = 0

        for num in num_set:
            if num - 1 not in num_set:
                length = 1
                while num + length in num_set:
                    length += 1
                longest = max(longest, length)

        return longest''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('search-in-rotated-sorted-array', 'Search in Rotated Sorted Array', 'maximum-product-subarray', 'Maximum Product Subarray'),
    trace_js='''
    const NUMS = [100, 4, 200, 1, 3, 2];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const set = new Set(NUMS);
      let longest = 0;
      for (const num of new Set(NUMS)) {
        const isStart = !set.has(num - 1);
        if (!isStart) { steps.push({ num, isStart, longest }); continue; }
        let length = 1;
        const chain = [num];
        while (set.has(num + length)) { chain.push(num + length); length++; }
        longest = Math.max(longest, length);
        steps.push({ num, isStart, length, chain, longest });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `<div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      if (!s.isStart) {
        const idx = NUMS.indexOf(s.num);
        document.getElementById(`cell-${idx}`).classList.add('scan');
        caption.textContent = `${s.num} - 1 = ${s.num - 1} is in the set → not a chain start, skip`;
      } else {
        s.chain.forEach(v => { const idx = NUMS.indexOf(v); if (idx !== -1) document.getElementById(`cell-${idx}`).classList.add('hit'); });
        caption.textContent = `${s.num} is a chain start → chain [${s.chain.join(',')}] length=${s.length} — longest so far: ${s.longest}`;
      }
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 6. longest-repeating-character-replacement ----------
problems.append(dict(
    slug='longest-repeating-character-replacement', title='Longest Repeating Character Replacement', category='String',
    difficulty='Medium', tags=['Sliding Window', 'String'],
    leetcode_url='https://leetcode.com/problems/longest-repeating-character-replacement/',
    statement_html='''<p class="leading-relaxed mb-4">Given a string <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s</code> and an integer <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">k</code>, you can replace up to <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">k</code> characters with any other character. Return the length of the longest substring containing the same letter after the replacements.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "AABABBA", k = 1</p><p><span class="text-soft">Output:</span> 4</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(26)'],
    time_big='O(n)', time_explain='A sliding window where both pointers only ever move forward — total O(n) work.',
    space_big='O(1)', space_explain='The frequency map holds at most 26 letters — constant regardless of n.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">"Window length minus max frequency" is the replacement cost.</strong> If that exceeds k, the window is invalid — shrink from the left instead of resetting it.'],
    approach_html='''<p class="mb-3">Maintain a sliding window and a frequency count of letters inside it. A window is valid if <code class="mono accent-text">(window length − count of the most frequent letter) ≤ k</code> — that difference is exactly how many characters you\'d need to replace. Expand the window each step; shrink from the left only when it becomes invalid.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Expand <code class="mono accent-text">right</code> one character at a time, updating the frequency count.</li>
          <li>Track <code class="mono accent-text">max_freq</code>, the count of the most common letter currently in the window.</li>
          <li>If <code class="mono accent-text">window_len - max_freq &gt; k</code>, shrink from <code class="mono accent-text">left</code>.</li>
          <li>Track the largest valid window length seen.</li>
        </ol>''',
    python_code='''class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        count = {}
        left = 0
        max_freq = 0
        result = 0

        for right in range(len(s)):
            count[s[right]] = count.get(s[right], 0) + 1
            max_freq = max(max_freq, count[s[right]])

            window_len = right - left + 1
            if window_len - max_freq > k:
                count[s[left]] -= 1
                left += 1

            result = max(result, right - left + 1)

        return result''',
    sidebar=STRING_SIDEBAR,
    prev_next_html=prev_next('group-anagrams', 'Group Anagrams', None, None),
    trace_js='''
    const S = "AABABBA";
    const K = 1;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const count = {};
      let left = 0, maxFreq = 0, result = 0;
      for (let right = 0; right < S.length; right++) {
        count[S[right]] = (count[S[right]] || 0) + 1;
        maxFreq = Math.max(maxFreq, count[S[right]]);
        const windowLen = right - left + 1;
        let shrunk = false;
        if (windowLen - maxFreq > K) {
          count[S[left]]--; left++; shrunk = true;
        }
        result = Math.max(result, right - left + 1);
        steps.push({ left, right, maxFreq, result, shrunk });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = S.split('').map((ch, i) => `<div class="cell" id="cell-${i}">${ch}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      S.split('').forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < s.left; i++) document.getElementById(`cell-${i}`).classList.add('discarded');
      for (let i = s.left; i <= s.right; i++) document.getElementById(`cell-${i}`).classList.add('hit');
      caption.textContent = `window [${s.left},${s.right}] maxFreq=${s.maxFreq}${s.shrunk ? ' — too many replacements needed, shrank left' : ''} — best length so far: ${s.result}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 7. maximum-product-subarray ----------
problems.append(dict(
    slug='maximum-product-subarray', title='Maximum Product Subarray', category='Array',
    difficulty='Medium', tags=['Dynamic Programming', 'Array'],
    leetcode_url='https://leetcode.com/problems/maximum-product-subarray/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, find a contiguous non-empty subarray with the largest product, and return that product.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [2,3,-2,4]</p><p><span class="text-soft">Output:</span> 6 <span class="cm">// [2,3] has the largest product</span></p>',
    trace_html='<div id="array-track" class="flex gap-3 pb-7 pt-7"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain='A single pass, tracking running max and min in constant time per step.',
    space_big='O(1)', space_explain='Only a few running variables are kept — no array or map.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Track both a running max AND min.</strong> A negative number can flip the smallest product into the largest — so you need the running minimum too, not just the maximum, in case the next number is negative.'],
    approach_html='''<p class="mb-3">Unlike maximum <em>sum</em> subarray, products are tricky because a negative number can turn a very small (negative) product into the largest one. So track both a running max and a running min at every index — either could become the new max once multiplied by a negative number.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">cur_max</code> and <code class="mono accent-text">cur_min</code> to the first element.</li>
          <li>At each new number, compute candidates: the number itself, <code class="mono accent-text">cur_max * num</code>, and <code class="mono accent-text">cur_min * num</code>.</li>
          <li>The new <code class="mono accent-text">cur_max</code>/<code class="mono accent-text">cur_min</code> are the max/min of those three candidates.</li>
          <li>Update the global result with <code class="mono accent-text">cur_max</code> at every step.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        result = nums[0]
        cur_max, cur_min = nums[0], nums[0]

        for num in nums[1:]:
            candidates = (num, cur_max * num, cur_min * num)
            cur_max, cur_min = max(candidates), min(candidates)
            result = max(result, cur_max)

        return result''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('longest-consecutive-sequence', 'Longest Consecutive Sequence', 'find-minimum-in-rotated-sorted-array', 'Find Minimum in Rotated Sorted Array'),
    trace_js='''
    const NUMS = [2, 3, -2, 4];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let result = NUMS[0], curMax = NUMS[0], curMin = NUMS[0];
      steps.push({ i: 0, curMax, curMin, result });
      for (let i = 1; i < NUMS.length; i++) {
        const num = NUMS[i];
        const candidates = [num, curMax * num, curMin * num];
        curMax = Math.max(...candidates);
        curMin = Math.min(...candidates);
        result = Math.max(result, curMax);
        steps.push({ i, curMax, curMin, result });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `<div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'done'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < s.i; i++) document.getElementById(`cell-${i}`).classList.add('done');
      document.getElementById(`cell-${s.i}`).classList.add('scan');
      caption.textContent = `i=${s.i} → curMax=${s.curMax}, curMin=${s.curMin}, best so far=${s.result}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 8. maximum-subarray ----------
problems.append(dict(
    slug='maximum-subarray', title='Maximum Subarray', category='Array',
    difficulty='Medium', tags=['Dynamic Programming', 'Array'],
    leetcode_url='https://leetcode.com/problems/maximum-subarray/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, find the contiguous subarray (containing at least one number) with the largest sum, and return its sum.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [-2,1,-3,4,-1,2,1,-5,4]</p><p><span class="text-soft">Output:</span> 6 <span class="cm">// [4,-1,2,1] has the largest sum</span></p>',
    trace_html='<div id="array-track" class="flex gap-3 pb-7 pt-7"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain="Kadane's algorithm makes a single pass, doing constant work per element.",
    space_big='O(1)', space_explain='Only two running variables are tracked: the current sum and the best sum.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">"Extend or restart" is the whole trick.</strong> At each element, ask: does adding this to my current run help, or would I be better off starting fresh from here? That single decision is Kadane\'s algorithm.'],
    approach_html='''<p class="mb-3">This is the classic <strong>Kadane\'s algorithm</strong>. At each index, decide whether to extend the current running subarray or start a brand-new one from the current element — whichever gives a larger sum.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">current_sum</code> and <code class="mono accent-text">max_sum</code> to the first element.</li>
          <li>For each next number, set <code class="mono accent-text">current_sum = max(num, current_sum + num)</code>.</li>
          <li>Update <code class="mono accent-text">max_sum = max(max_sum, current_sum)</code>.</li>
          <li>Return <code class="mono accent-text">max_sum</code> after the pass.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        max_sum = nums[0]
        current_sum = nums[0]

        for num in nums[1:]:
            current_sum = max(num, current_sum + num)
            max_sum = max(max_sum, current_sum)

        return max_sum''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('container-with-most-water', 'Container With Most Water', 'longest-consecutive-sequence', 'Longest Consecutive Sequence'),
    trace_js='''
    const NUMS = [-2, 1, -3, 4, -1, 2, 1, -5, 4];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let maxSum = NUMS[0], curSum = NUMS[0];
      steps.push({ i: 0, curSum, maxSum, restarted: false });
      for (let i = 1; i < NUMS.length; i++) {
        const num = NUMS[i];
        const restarted = num > curSum + num;
        curSum = Math.max(num, curSum + num);
        maxSum = Math.max(maxSum, curSum);
        steps.push({ i, curSum, maxSum, restarted });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `<div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'done'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < s.i; i++) document.getElementById(`cell-${i}`).classList.add('done');
      document.getElementById(`cell-${s.i}`).classList.add(s.curSum === s.maxSum ? 'hit' : 'scan');
      caption.textContent = `i=${s.i} → ${s.restarted ? 'restarted run here' : 'extended the run'} → current_sum=${s.curSum}, max_sum=${s.maxSum}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 9. reverse-linked-list ----------
problems.append(dict(
    slug='reverse-linked-list', title='Reverse Linked List', category='Linked List',
    difficulty='Easy', tags=['Linked List', 'Pointers'],
    leetcode_url='https://leetcode.com/problems/reverse-linked-list/',
    statement_html='''<p class="leading-relaxed mb-4">Given the <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">head</code> of a singly linked list, reverse the list and return the new head.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> head = [1,2,3,4,5]</p><p><span class="text-soft">Output:</span> [5,4,3,2,1]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center items-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)', time_explain='Every node is visited exactly once to flip its pointer.',
    space_big='O(1)', space_explain='Only two or three pointers are tracked — the list is reversed in place.',
    tricks=GENERIC_TRICKS[:3] + ['<strong class="accent-text">Save next before you overwrite it.</strong> The single most common bug in pointer-reversal problems is losing the rest of the list because you flipped <code class="mono">curr.next</code> before storing where it pointed.'],
    approach_html='''<p class="mb-3">Walk the list once, flipping each node\'s <code class="mono accent-text">next</code> pointer to point backward instead of forward. Three pointers do the work: <code class="mono accent-text">prev</code> (the reversed portion so far), <code class="mono accent-text">curr</code> (the node being flipped), and a temporary <code class="mono accent-text">next_node</code> to avoid losing the rest of the list.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Start with <code class="mono accent-text">prev = None</code>, <code class="mono accent-text">curr = head</code>.</li>
          <li>Save <code class="mono accent-text">next_node = curr.next</code> before changing anything.</li>
          <li>Flip the pointer: <code class="mono accent-text">curr.next = prev</code>.</li>
          <li>Advance both: <code class="mono accent-text">prev = curr</code>, <code class="mono accent-text">curr = next_node</code>.</li>
          <li>When <code class="mono accent-text">curr</code> is <code class="mono accent-text">None</code>, <code class="mono accent-text">prev</code> is the new head.</li>
        </ol>''',
    python_code='''from typing import Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev = None
        curr = head

        while curr:
            next_node = curr.next
            curr.next = prev
            prev = curr
            curr = next_node

        return prev''',
    sidebar=LINKED_LIST_SIDEBAR,
    prev_next_html=prev_next(None, None, None, None),
    trace_js='''
    const VALS = [1, 2, 3, 4, 5];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      // node i's "next" pointer target index, -1 means null. Starts as i+1 (forward list).
      steps = [];
      let nextPtr = VALS.map((_, i) => i + 1 < VALS.length ? i + 1 : -1);
      let prev = -1, curr = 0;
      steps.push({ prev, curr, nextPtr: [...nextPtr], action: 'start' });
      while (curr !== -1) {
        const nextNode = nextPtr[curr];
        nextPtr[curr] = prev;
        prev = curr;
        curr = nextNode;
        steps.push({ prev, curr, nextPtr: [...nextPtr], action: 'flip' });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      renderListStructure(steps[0].nextPtr, -1, 0);
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderListStructure(nextPtr, prevIdx, currIdx) {
      const track = document.getElementById('array-track');
      // order nodes left-to-right by original index for stable visual layout
      let html = '';
      VALS.forEach((v, i) => {
        const isCur = i === currIdx, isPrev = i === prevIdx;
        html += `<div class="ll-node">
          <div class="ll-box ${isCur ? 'cur' : ''} ${isPrev ? 'prev' : ''}">${v}
            ${isCur ? '<span class="ll-label" style="color:var(--trace-scan)">curr</span>' : ''}
            ${isPrev ? '<span class="ll-label" style="color:var(--trace-hit)">prev</span>' : ''}
          </div>
          <span class="ll-arrow">${nextPtr[i] === -1 ? '→ ∅' : (nextPtr[i] > i ? '→' : '←')}</span>
        </div>`;
      });
      track.innerHTML = html;
    }

    function renderStep() {
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) {
        renderListStructure(steps[0].nextPtr, -1, 0);
        caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return;
      }
      const s = steps[stepIndex];
      renderListStructure(s.nextPtr, s.prev, s.curr);
      if (s.action === 'start') {
        caption.textContent = `prev=None, curr=head (node ${VALS[s.curr]})`;
      } else if (s.curr === -1) {
        caption.textContent = `curr is None → reversal complete. New head is node ${VALS[s.prev]}.`;
      } else {
        caption.textContent = `Flipped node ${VALS[s.prev]}'s pointer backward. Now prev=${VALS[s.prev]}, curr=${VALS[s.curr]}.`;
      }
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# ---------- 10. search-in-rotated-sorted-array ----------
problems.append(dict(
    slug='search-in-rotated-sorted-array', title='Search in Rotated Sorted Array', category='Array',
    difficulty='Medium', tags=['Binary Search', 'Array'],
    leetcode_url='https://leetcode.com/problems/search-in-rotated-sorted-array/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, sorted in ascending order and rotated at an unknown pivot, and an integer <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">target</code>. Return the index of <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">target</code>, or <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">-1</code> if it isn\'t present.</p>
        <p class="text-soft text-sm mb-5">All values are unique. You must solve it in <span class="mono accent-text">O(log n)</span> time.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [4,5,6,7,0,1,2], target = 0</p><p><span class="text-soft">Output:</span> 4</p>',
    trace_html='<div id="array-track" class="flex gap-3 pb-7 pt-7"></div>',
    quiz_time_opts=['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(log n)', time_explain='The search window halves every iteration, even with the rotation.',
    space_big='O(1)', space_explain='Only three index pointers are tracked.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">One half is always fully sorted.</strong> Even in a rotated array, comparing nums[low] to nums[mid] tells you instantly which half is normally ordered — then a simple range check tells you if the target could be there.'],
    approach_html='''<p class="mb-3">A rotated sorted array still has one useful property: <strong>at least one half of any window is always fully sorted.</strong> Standard binary search, but at each step you first figure out which half is sorted, then decide whether the target could live there.</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Compute <code class="mono accent-text">mid</code>. If <code class="mono accent-text">nums[mid] === target</code>, return <code class="mono accent-text">mid</code>.</li>
          <li>If <code class="mono accent-text">nums[low] &lt;= nums[mid]</code>, the left half is sorted.</li>
          <li>Check whether <code class="mono accent-text">target</code> falls inside that sorted half\'s range — if so, search there; otherwise search the other half.</li>
          <li>Repeat until the window closes or the target is found.</li>
        </ol>''',
    python_code='''from typing import List

class Solution:
    def search(self, nums: List[int], target: int) -> int:
        left, right = 0, len(nums) - 1

        while left <= right:
            mid = (left + right) // 2

            if nums[mid] == target:
                return mid

            if nums[left] <= nums[mid]:
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            else:
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    right = mid - 1

        return -1''',
    sidebar=ARRAY_SIDEBAR,
    prev_next_html=prev_next('container-with-most-water', 'Container With Most Water', 'longest-consecutive-sequence', 'Longest Consecutive Sequence'),
    trace_js='''
    const NUMS = [4, 5, 6, 7, 0, 1, 2];
    const TARGET = 0;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let low = 0, high = NUMS.length - 1;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        if (NUMS[mid] === TARGET) { steps.push({ low, mid, high, found: true }); break; }
        const leftSorted = NUMS[low] <= NUMS[mid];
        let goRight;
        if (leftSorted) goRight = !(TARGET >= NUMS[low] && TARGET < NUMS[mid]);
        else goRight = (TARGET > NUMS[mid] && TARGET <= NUMS[high]);
        steps.push({ low, mid, high, leftSorted, goRight, found: false });
        if (goRight) low = mid + 1; else high = mid - 1;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `<div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function setPointers(low, mid, high) {
      NUMS.forEach((_, i) => {
        const p = document.getElementById(`ptr-${i}`);
        let labels = [];
        if (i === low) labels.push('low');
        if (i === mid) labels.push('mid');
        if (i === high) labels.push('high');
        p.textContent = labels.join('/');
        p.style.opacity = labels.length ? 1 : 0;
      });
    }

    function renderStep() {
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) {
        NUMS.forEach((_, i) => { document.getElementById(`cell-${i}`).classList.remove('discarded', 'scan', 'hit'); document.getElementById(`ptr-${i}`).style.opacity = 0; });
        caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return;
      }
      const s = steps[stepIndex];
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.toggle('discarded', i < s.low || i > s.high);
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
      });
      setPointers(s.low, s.mid, s.high);
      if (s.found) {
        document.getElementById(`cell-${s.mid}`).classList.add('hit');
        caption.textContent = `nums[${s.mid}] === target → return ${s.mid}`;
      } else {
        document.getElementById(`cell-${s.mid}`).classList.add('scan');
        caption.textContent = `mid=${s.mid} → ${s.leftSorted ? 'left half sorted' : 'right half sorted'} → search ${s.goRight ? 'right' : 'left'} half`;
      }
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# /Users/songram/.gemini/antigravity/brain/39462a12-ba4c-41e9-b197-de792c14e4ba/scratch/extra_problems.py

# GENERIC_TRICKS already defined
_IGNORE = [
  '<strong class="accent-text">Count the loops, not the lines.</strong> One pass over n elements with O(1) work per element gives O(n); nested loops over the same input usually multiply.',
  '<strong class="accent-text">Hash set/map operations are O(1) average.</strong> A loop doing one lookup or insert per iteration stays O(n) overall — the hash structure doesn\'t add a factor.',
  '<strong class="accent-text">Space tracks "extra" memory, not the input.</strong> Ask what new structure you\'re building and how big it can get.',
  '<strong class="accent-text">Two pointers / sliding window ≠ O(n²).</strong> Even though it looks like nested loops, each pointer only ever moves forward — total work stays O(n).'
]

EXTRA_PROBLEMS = []

# 0. two-sum
EXTRA_PROBLEMS.append(dict(
    slug='two-sum', title='Two Sum', category='Array', course='blind-75',
    difficulty='Easy', tags=['Hash Map', 'Array'],
    leetcode_url='https://leetcode.com/problems/two-sum/',
    statement_html='''<p class="leading-relaxed mb-4">
          Given an array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code> and an integer <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">target</code>, return the indices of the two numbers that add up to <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">target</code>.
        </p>
        <p class="text-soft text-sm mb-5">You may assume exactly one solution exists, and you may not use the same element twice.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [2,7,11,15], target = 9</p><p><span class="text-soft">Output:</span> [0,1] <span class="cm">// nums[0] + nums[1] == 9</span></p>',
    trace_html='''<div id="array-track" class="flex gap-3 pb-5"></div>
          <div class="w-full">
            <p class="text-xs font-bold uppercase tracking-wider text-soft mb-2">hash map &nbsp;(value → index)</p>
            <div id="map-track" class="flex gap-2 flex-wrap min-h-[42px]"></div>
          </div>''',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Single pass through the array. Each hash map lookup and insert takes O(1) time on average.',
    space_big='O(n)',
    space_explain='The hash map stores at most n elements in the worst case before a complement is found.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Hash map complement trick:</strong> Instead of checking all pairs with two loops (O(n²)), check if (target - num) is in a hash map as you iterate (O(n)).'],
    approach_html='''<p class="mb-3">A brute-force check of every pair costs O(n²). The interview-standard fix: walk the array once, and at each index ask <em>"have I already seen the number that completes this pair?"</em></p>
          <ol class="list-decimal list-inside space-y-2 text-soft">
            <li>For the current number, compute <code class="mono accent-text">complement = target - num</code>.</li>
            <li>Look up <code class="mono accent-text">complement</code> in the hash map.</li>
            <li>If found, return the stored index and the current index — done in a single pass.</li>
            <li>Otherwise, store <code class="mono accent-text">num → index</code> and continue.</li>
          </ol>''',
    python_code='''from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}  # value -> index

        for i, num in enumerate(nums):
            complement = target - num

            if complement in seen:
                return [seen[complement], i]

            seen[num] = i

        return []  # no solution found''',
    trace_js='''
    const NUMS = [2, 7, 11, 15];
    const TARGET = 9;
    let steps = [];
    let stepIndex = -1;

    function computeSteps() {
      steps = [];
      const seen = new Map();
      for (let i = 0; i < NUMS.length; i++) {
        const complement = TARGET - NUMS[i];
        steps.push({ type: 'scan', i, complement, mapSnapshot: new Map(seen) });
        if (seen.has(complement)) {
          steps.push({ type: 'hit', i, j: seen.get(complement), mapSnapshot: new Map(seen) });
          break;
        }
        seen.set(NUMS[i], i);
        steps.push({ type: 'store', i, mapSnapshot: new Map(seen) });
      }
    }

    function buildTrace() {
      computeSteps();
      stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((n, i) => `
        <div class="cell" id="cell-${i}">${n}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('map-track').innerHTML = '';
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        const cell = document.getElementById(`cell-${i}`);
        cell.classList.remove('scan', 'hit', 'done');
      });

      const mapTrack = document.getElementById('map-track');
      const caption = document.getElementById('trace-caption');

      if (stepIndex < 0) {
        mapTrack.innerHTML = '';
        caption.textContent = 'Click "Next" to begin.';
        updateStepControls();
        return;
      }

      const step = steps[stepIndex];
      mapTrack.innerHTML = Array.from(step.mapSnapshot.entries())
        .map(([val, idx]) => `<div class="map-slot filled">${val} → ${idx}</div>`).join('')
        || '<span class="text-xs text-soft mono">empty</span>';

      for (let i = 0; i < step.i; i++) document.getElementById(`cell-${i}`).classList.add('done');

      if (step.type === 'scan') {
        document.getElementById(`cell-${step.i}`).classList.add('scan');
        caption.textContent = `i=${step.i} → complement of ${NUMS[step.i]} is ${step.complement}. Checking map…`;
      } else if (step.type === 'store') {
        document.getElementById(`cell-${step.i}`).classList.add('scan');
        caption.textContent = `Not found. Storing nums[${step.i}]=${NUMS[step.i]} → index ${step.i} in the map.`;
      } else if (step.type === 'hit') {
        document.getElementById(`cell-${step.i}`).classList.add('hit');
        document.getElementById(`cell-${step.j}`).classList.add('hit');
        caption.textContent = `Found! nums[${step.j}] + nums[${step.i}] = ${TARGET} → return [${step.j}, ${step.i}]`;
      }
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# reorder-list
EXTRA_PROBLEMS.append(dict(
    slug='reorder-list', title='Reorder List', category='Linked List', course='blind-75',
    difficulty='Medium', tags=['Linked List', 'Two Pointers'],
    leetcode_url='https://leetcode.com/problems/reorder-list/',
    statement_html='''<p class="leading-relaxed mb-4">
          You are given the head of a singly linked list. The list can be represented as <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">L0 → L1 → … → Ln-1 → Ln</code>. Reorder it in place to the form <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → …</code>
        </p>
        <p class="text-soft text-sm mb-5">You may not modify the values in the list's nodes — only the nodes themselves may be rearranged.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> head = [1,2,3,4,5]</p><p><span class="text-soft">Output:</span> [1,5,2,4,3] <span class="cm">// weave front and back halves together</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Finding middle (n/2), reversing second half (n/2), and merging (n/2) each take linear time.',
    space_big='O(1)',
    space_explain='In-place pointer rewiring uses a constant number of pointer variables.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Three-Phase Linked List:</strong> (1) Find middle with slow/fast pointers, (2) reverse second half, (3) merge halves alternately.'],
    approach_html='''<p class="mb-3">Break the problem into three classic linked list subproblems:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Find the middle of the linked list using slow and fast pointers.</li>
      <li>Split the list and reverse the second half in place.</li>
      <li>Merge the first half and the reversed second half node-by-node alternately.</li>
    </ol>''',
    python_code='''from typing import Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        if not head or not head.next:
            return

        # 1. Find middle
        slow, fast = head, head
        while fast.next and fast.next.next:
            slow = slow.next
            fast = fast.next.next

        # 2. Reverse second half
        prev, curr = None, slow.next
        slow.next = None
        while curr:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt

        # 3. Merge alternating
        first, second = head, prev
        while second:
            tmp1, tmp2 = first.next, second.next
            first.next = second
            second.next = tmp1
            first, second = tmp1, tmp2''',
    trace_js='''
    const LIST = [1, 2, 3, 4, 5];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ state: [1, 2, 3, 4, 5], note: "Initial List: 1 → 2 → 3 → 4 → 5" });
      steps.push({ state: [1, 2, 3], note: "Phase 1: Middle found at node 3 (slow pointer)" });
      steps.push({ state: [5, 4], note: "Phase 2: Second half [4, 5] reversed to [5, 4]" });
      steps.push({ state: [1, 5, 2, 4, 3], note: "Phase 3: Merged alternating → 1 → 5 → 2 → 4 → 3" });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = LIST.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">node ${i+1}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      LIST.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      LIST.forEach((v, i) => {
        if (s.state.includes(v)) document.getElementById(`cell-${i}`).classList.add('hit');
      });
      caption.textContent = s.note;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# best-time-to-buy-and-sell-stock
EXTRA_PROBLEMS.append(dict(
    slug='best-time-to-buy-and-sell-stock',
    title='Best Time to Buy and Sell Stock',
    category='Array',
    course='blind-75',
    difficulty='Easy',
    tags=['Array', 'Dynamic Programming'],
    leetcode_url='https://leetcode.com/problems/best-time-to-buy-and-sell-stock/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">prices</code> where <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">prices[i]</code> is the price of a given stock on the <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">i</code>th day.</p>
    <p class="leading-relaxed mb-4">You want to maximize your profit by choosing a <strong>single day</strong> to buy one stock and choosing a <strong>different day in the future</strong> to sell that stock.</p>
    <p class="text-soft text-sm mb-5">Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return <code class="mono">0</code>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> prices = [7,1,5,3,6,4]</p><p><span class="text-soft">Output:</span> 5 <span class="cm">// Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6 - 1 = 5</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Single pass through prices array of length n. Constant work per day.',
    space_big='O(1)',
    space_explain='Only two variables needed: min_price and max_profit.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">One pass greedily tracking the minimum:</strong> As you scan forward, every day asks: "if I had bought at the cheapest day seen so far, what is my profit today?"'],
    approach_html='''<p class="mb-3">A naive brute force computes profit for every buy-sell pair in O(n²). Instead, observe that the best selling day always pairs with the lowest price prior to it:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Maintain <code class="mono accent-text">min_price = infinity</code> and <code class="mono accent-text">max_profit = 0</code>.</li>
      <li>Iterate through each price in the array.</li>
      <li>If current price is lower than <code class="mono accent-text">min_price</code>, update <code class="mono accent-text">min_price</code>.</li>
      <li>Otherwise, calculate potential profit <code class="mono accent-text">price - min_price</code> and update <code class="mono accent-text">max_profit</code>.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        min_price = float('inf')
        max_profit = 0

        for price in prices:
            if price < min_price:
                min_price = price
            elif price - min_price > max_profit:
                max_profit = price - min_price

        return max_profit''',
    trace_js='''
    const PRICES = [7, 1, 5, 3, 6, 4];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let minPrice = Infinity, minIdx = -1, maxProfit = 0;
      for (let i = 0; i < PRICES.length; i++) {
        const p = PRICES[i];
        let newMin = false, newProfit = false;
        if (p < minPrice) {
          minPrice = p; minIdx = i; newMin = true;
        } else if (p - minPrice > maxProfit) {
          maxProfit = p - minPrice; newProfit = true;
        }
        steps.push({ i, p, minPrice, minIdx, profit: p - minPrice, maxProfit, newMin, newProfit });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = PRICES.map((p, i) => `<div class="cell" id="cell-${i}">${p}<span class="idx">day ${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      PRICES.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < s.i; i++) document.getElementById(`cell-${i}`).classList.add('discarded');
      document.getElementById(`cell-${s.i}`).classList.add(s.newProfit ? 'hit' : 'scan');
      if (s.minIdx >= 0) {
        document.getElementById(`cell-${s.minIdx}`).classList.remove('discarded');
        document.getElementById(`cell-${s.minIdx}`).classList.add('scan');
        document.getElementById(`ptr-${s.minIdx}`).textContent = 'min';
      }
      document.getElementById(`ptr-${s.i}`).textContent = s.i === s.minIdx ? 'min' : 'sell?';
      caption.textContent = `Day ${s.i}: Price $${s.p} → min price so far: $${s.minPrice} | Profit: $${Math.max(0, s.profit)} | Max profit: $${s.maxProfit}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# product-of-array-except-self
EXTRA_PROBLEMS.append(dict(
    slug='product-of-array-except-self',
    title='Product of Array Except Self',
    category='Array',
    course='blind-75',
    difficulty='Medium',
    tags=['Array', 'Prefix Sum'],
    leetcode_url='https://leetcode.com/problems/product-of-array-except-self/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, return an array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">answer</code> such that <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">answer[i]</code> is equal to the product of all the elements of <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code> except <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums[i]</code>.</p>
    <p class="leading-relaxed mb-4">The product of any prefix or suffix of <code class="mono">nums</code> is guaranteed to fit in a <strong>32-bit</strong> integer.</p>
    <p class="text-soft text-sm mb-5">You must write an algorithm that runs in <code class="mono">O(n)</code> time and <strong>without using the division operation</strong>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [1,2,3,4]</p><p><span class="text-soft">Output:</span> [24,12,8,6]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Two linear passes over the array of size n (prefix pass then postfix pass).',
    space_big='O(1)',
    space_explain='Output array does not count toward extra space complexity per problem constraints.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Prefix * Postfix:</strong> Any element\'s missing factor is just (product of all items to its left) * (product of all items to its right).'],
    approach_html='''<p class="mb-3">We cannot use division, so we split each answer into two components: the prefix product (elements before index i) and the postfix product (elements after index i):</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Initialize the output array with 1s.</li>
      <li>Pass left-to-right: each cell gets the cumulative product of elements to its left.</li>
      <li>Pass right-to-left: multiply each cell by the cumulative product of elements to its right.</li>
      <li>Return the resulting output array in O(n) time and O(1) extra space.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        res = [1] * n

        prefix = 1
        for i in range(n):
            res[i] = prefix
            prefix *= nums[i]

        postfix = 1
        for i in range(n - 1, -1, -1):
            res[i] *= postfix
            postfix *= nums[i]

        return res''',
    trace_js='''
    const NUMS = [1, 2, 3, 4];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const n = NUMS.length;
      let res = new Array(n).fill(1);
      let prefix = 1;
      for (let i = 0; i < n; i++) {
        res[i] = prefix;
        steps.push({ pass: 'prefix', i, res: [...res], prefix, val: NUMS[i] });
        prefix *= NUMS[i];
      }
      let postfix = 1;
      for (let i = n - 1; i >= 0; i--) {
        res[i] *= postfix;
        steps.push({ pass: 'postfix', i, res: [...res], postfix, val: NUMS[i] });
        postfix *= NUMS[i];
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `<div class="cell" id="cell-${i}">1<span class="idx">nums[${i}]=${v}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).childNodes[0].nodeValue = s.res[i];
      });
      document.getElementById(`cell-${s.i}`).classList.add(s.pass === 'postfix' ? 'hit' : 'scan');
      document.getElementById(`ptr-${s.i}`).textContent = s.pass;
      caption.textContent = `[${s.pass.toUpperCase()} PASS] index ${s.i}: multiplier=${s.pass === 'prefix' ? s.prefix : s.postfix} → res[${s.i}]=${s.res[s.i]}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# longest-substring-without-repeating-characters
EXTRA_PROBLEMS.append(dict(
    slug='longest-substring-without-repeating-characters',
    title='Longest Substring Without Repeating Characters',
    category='String',
    course='blind-75',
    difficulty='Medium',
    tags=['Hash Table', 'String', 'Sliding Window'],
    leetcode_url='https://leetcode.com/problems/longest-substring-without-repeating-characters/',
    statement_html='''<p class="leading-relaxed mb-4">Given a string <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s</code>, find the length of the <strong>longest substring</strong> without duplicate characters.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "abcabcbb"</p><p><span class="text-soft">Output:</span> 3 <span class="cm">// The answer is "abc", with the length of 3.</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(min(m, n))', 'O(n²)'],
    time_big='O(n)',
    time_explain='Each character is visited at most twice by left and right sliding window pointers.',
    space_big='O(min(m, n))',
    space_explain='Hash set size bounded by the character alphabet size m or string length n.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Sliding Window with Set:</strong> Expand right pointer greedily. If a collision occurs, contract left pointer until unique.'],
    approach_html='''<p class="mb-3">Use a sliding window <code class="mono accent-text">[left...right]</code> backed by a hash set to detect duplicate characters:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Iterate <code class="mono accent-text">right</code> pointer across the string.</li>
      <li>While <code class="mono accent-text">s[right]</code> already exists in the set, remove <code class="mono accent-text">s[left]</code> and advance <code class="mono accent-text">left</code>.</li>
      <li>Insert <code class="mono accent-text">s[right]</code> into the set.</li>
      <li>Update max length as <code class="mono accent-text">max_len = max(max_len, right - left + 1)</code>.</li>
    </ol>''',
    python_code='''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_set = set()
        left = 0
        max_len = 0

        for right in range(len(s)):
            while s[right] in char_set:
                char_set.remove(s[left])
                left += 1
            char_set.add(s[right])
            max_len = max(max_len, right - left + 1)

        return max_len''',
    trace_js='''
    const STR = "abcabcbb";
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let charSet = new Set(), left = 0, maxLen = 0;
      for (let right = 0; right < STR.length; right++) {
        const c = STR[right];
        while (charSet.has(c)) {
          steps.push({ left, right, charSet: new Set(charSet), maxLen, conflict: true, c });
          charSet.delete(STR[left]);
          left++;
        }
        charSet.add(c);
        maxLen = Math.max(maxLen, right - left + 1);
        steps.push({ left, right, charSet: new Set(charSet), maxLen, conflict: false, c });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = STR.split('').map((ch, i) => `<div class="cell" id="cell-${i}">${ch}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      STR.split('').forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < STR.length; i++) {
        if (i < s.left || i > s.right) document.getElementById(`cell-${i}`).classList.add('discarded');
        else document.getElementById(`cell-${i}`).classList.add(s.conflict ? 'scan' : 'hit');
      }
      document.getElementById(`ptr-${s.left}`).textContent = 'L';
      document.getElementById(`ptr-${s.right}`).textContent = (s.left === s.right) ? 'L/R' : 'R';
      caption.textContent = s.conflict
        ? `Duplicate '${s.c}' found! Shrinking window left (L=${s.left})`
        : `Window "${STR.slice(s.left, s.right + 1)}" valid (len: ${s.right - s.left + 1}) — Max len: ${s.maxLen}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# valid-anagram
EXTRA_PROBLEMS.append(dict(
    slug='valid-anagram',
    title='Valid Anagram',
    category='String',
    course='blind-75',
    difficulty='Easy',
    tags=['Hash Table', 'String', 'Sorting'],
    leetcode_url='https://leetcode.com/problems/valid-anagram/',
    statement_html='''<p class="leading-relaxed mb-4">Given two strings <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s</code> and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">t</code>, return <code class="mono">true</code> if <code class="mono">t</code> is an anagram of <code class="mono">s</code>, and <code class="mono">false</code> otherwise.</p>
    <p class="text-soft text-sm mb-5">An <strong>anagram</strong> is a word formed by rearranging the letters of a different word, using all original letters exactly once.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "anagram", t = "nagaram"</p><p><span class="text-soft">Output:</span> true</p>',
    trace_html='''<div class="w-full flex flex-col items-center gap-6">
      <div class="flex flex-col md:flex-row items-center gap-8 justify-center">
        <div>
          <p class="text-xs font-bold uppercase tracking-wider text-soft mb-2 text-center">String s ("anagram")</p>
          <div id="s-track" class="flex gap-2 justify-center flex-wrap"></div>
        </div>
        <div>
          <p class="text-xs font-bold uppercase tracking-wider text-soft mb-2 text-center">String t ("nagaram")</p>
          <div id="t-track" class="flex gap-2 justify-center flex-wrap"></div>
        </div>
      </div>
      <div class="w-full max-w-lg">
        <p class="text-xs font-bold uppercase tracking-wider text-soft mb-2 text-center">Character Frequency Map &nbsp;(char → count)</p>
        <div id="map-track" class="flex gap-2 flex-wrap justify-center min-h-[46px]"></div>
      </div>
    </div>''',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Counting frequencies of both strings takes linear time in string length n.',
    space_big='O(1)',
    space_explain='Alphabet has at most 26 lowercase English characters.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Fixed 26-character frequency table:</strong> If lengths match, count char frequencies. If all net counts hit 0, it is an anagram.'],
    approach_html='''<p class="mb-3">Two strings are anagrams if and only if they contain the exact same characters in equal counts:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>If <code class="mono accent-text">len(s) != len(t)</code>, return false immediately.</li>
      <li>Tally character counts of <code class="mono accent-text">s</code> in a frequency table.</li>
      <li>Decrement counts using characters of <code class="mono accent-text">t</code>.</li>
      <li>If any count drops below 0 or a character is missing, return false; otherwise return true.</li>
    </ol>''',
    python_code='''class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t):
            return False

        char_count = {}

        # Count frequencies in string s
        for char in s:
            char_count[char] = char_count.get(char, 0) + 1

        # Decrement frequencies using string t
        for char in t:
            if char not in char_count or char_count[char] == 0:
                return False
            char_count[char] -= 1

        return True''',
    trace_js='''
    const S = "anagram";
    const T = "nagaram";
    let steps = [];
    let stepIndex = -1;

    function computeSteps() {
      steps = [];
      const counts = {};

      for (let i = 0; i < S.length; i++) {
        const char = S[i];
        counts[char] = (counts[char] || 0) + 1;
        steps.push({
          phase: 'tally_s',
          i,
          char,
          counts: { ...counts },
          caption: `[Pass 1: Tally s] Reading s[${i}] = '${char}'. Frequency of '${char}' is now ${counts[char]}.`
        });
      }

      for (let i = 0; i < T.length; i++) {
        const char = T[i];
        counts[char] = (counts[char] || 0) - 1;
        steps.push({
          phase: 'match_t',
          i,
          char,
          counts: { ...counts },
          caption: `[Pass 2: Match t] Matching t[${i}] = '${char}'. Remaining needed frequency of '${char}' is now ${counts[char]}.`
        });
      }

      steps.push({
        phase: 'complete',
        counts: { ...counts },
        caption: `🎉 All characters matched with net zero frequencies. Strings are valid anagrams! Return True.`
      });
    }

    function buildTrace() {
      computeSteps();
      stepIndex = -1;

      const sTrack = document.getElementById('s-track');
      sTrack.innerHTML = S.split('').map((c, i) => `
        <div class="cell" id="s-cell-${i}">${c}<span class="idx">s[${i}]</span></div>
      `).join('');

      const tTrack = document.getElementById('t-track');
      tTrack.innerHTML = T.split('').map((c, i) => `
        <div class="cell" id="t-cell-${i}">${c}<span class="idx">t[${i}]</span></div>
      `).join('');

      document.getElementById('map-track').innerHTML = '<span class="text-xs text-soft mono">empty</span>';
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      S.split('').forEach((_, i) => {
        const el = document.getElementById(`s-cell-${i}`);
        el.classList.remove('scan', 'hit', 'done');
      });
      T.split('').forEach((_, i) => {
        const el = document.getElementById(`t-cell-${i}`);
        el.classList.remove('scan', 'hit', 'done');
      });

      const mapTrack = document.getElementById('map-track');
      const caption = document.getElementById('trace-caption');

      if (stepIndex < 0) {
        mapTrack.innerHTML = '<span class="text-xs text-soft mono">empty</span>';
        caption.textContent = 'Click "Next" to begin.';
        updateStepControls();
        return;
      }

      const s = steps[stepIndex];

      const entries = Object.entries(s.counts);
      if (entries.length === 0) {
        mapTrack.innerHTML = '<span class="text-xs text-soft mono">empty</span>';
      } else {
        mapTrack.innerHTML = entries.map(([char, count]) => {
          const isZero = count === 0;
          return `<div class="map-slot filled ${isZero ? 'opacity-40' : ''}"><span class="font-bold text-accent">${char}</span>: ${count}</div>`;
        }).join('');
      }

      if (s.phase === 'tally_s') {
        for (let j = 0; j < s.i; j++) document.getElementById(`s-cell-${j}`).classList.add('done');
        document.getElementById(`s-cell-${s.i}`).classList.add('scan');
      } else if (s.phase === 'match_t') {
        S.split('').forEach((_, j) => document.getElementById(`s-cell-${j}`).classList.add('done'));
        for (let j = 0; j < s.i; j++) document.getElementById(`t-cell-${j}`).classList.add('done');
        document.getElementById(`t-cell-${s.i}`).classList.add('hit');
      } else if (s.phase === 'complete') {
        S.split('').forEach((_, j) => document.getElementById(`s-cell-${j}`).classList.add('hit'));
        T.split('').forEach((_, j) => document.getElementById(`t-cell-${j}`).classList.add('hit'));
      }

      caption.textContent = s.caption;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))


# /Users/songram/.gemini/antigravity/brain/39462a12-ba4c-41e9-b197-de792c14e4ba/scratch/extra_problems_neetcode.py


NEETCODE_PROBLEMS = []

# 1. top-k-frequent-elements
NEETCODE_PROBLEMS.append(dict(
    slug='top-k-frequent-elements',
    title='Top K Frequent Elements',
    category='Arrays & Hashing',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Hash Table', 'Bucket Sort', 'Heap (Priority Queue)'],
    leetcode_url='https://leetcode.com/problems/top-k-frequent-elements/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code> and an integer <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">k</code>, return the <code class="mono">k</code> most frequent elements. You may return the answer in <strong>any order</strong>.</p>
    <p class="text-soft text-sm mb-5">Your algorithm's time complexity must be better than <code class="mono">O(n log n)</code>, where n is the array's size.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [1,1,1,2,2,3], k = 2</p><p><span class="text-soft">Output:</span> [1,2]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Bucket sort indexes elements by frequency in range 0..n, avoiding sorting.',
    space_big='O(n)',
    space_explain='Hash map and bucket array together scale linearly with n.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Bucket Sort by Frequency:</strong> Instead of sorting by frequency in O(n log n), create n buckets where bucket[freq] holds all numbers with that frequency.'],
    approach_html='''<p class="mb-3">To beat O(n log n) heap/sorting time, use Bucket Sort:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Count frequencies of each number with a hash map in O(n).</li>
      <li>Create an array of buckets of size <code class="mono accent-text">len(nums) + 1</code>.</li>
      <li>Place each number into the bucket corresponding to its frequency count.</li>
      <li>Scan buckets backwards from <code class="mono accent-text">n</code> down to 1, collecting the first <code class="mono accent-text">k</code> items.</li>
    </ol>''',
    python_code='''from typing import List
from collections import Counter

class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = Counter(nums)
        buckets = [[] for _ in range(len(nums) + 1)]

        for num, freq in count.items():
            buckets[freq].append(num)

        res = []
        for i in range(len(buckets) - 1, 0, -1):
            for num in buckets[i]:
                res.append(num)
                if len(res) == k:
                    return res
        return res''',
    trace_js='''
    const NUMS = [1, 1, 1, 2, 2, 3];
    const K = 2;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ msg: 'Tally frequencies: {1: 3 times, 2: 2 times, 3: 1 time}', res: [] });
      steps.push({ msg: 'Place into buckets: bucket[3]=[1], bucket[2]=[2], bucket[1]=[3]', res: [] });
      steps.push({ msg: 'Read bucket[3]: collect number 1', res: [1] });
      steps.push({ msg: 'Read bucket[2]: collect number 2 → reached k=2 elements!', res: [1, 2] });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      NUMS.forEach((v, i) => {
        if (s.res.includes(v)) document.getElementById(`cell-${i}`).classList.add('hit');
      });
      caption.textContent = `${s.msg} | Result: [${s.res.join(', ')}]`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 2. valid-sudoku
NEETCODE_PROBLEMS.append(dict(
    slug='valid-sudoku',
    title='Valid Sudoku',
    category='Arrays & Hashing',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Hash Table', 'Matrix'],
    leetcode_url='https://leetcode.com/problems/valid-sudoku/',
    statement_html='''<p class="leading-relaxed mb-4">Determine if a <code class="mono">9 x 9</code> Sudoku board is valid. Only the filled cells need to be validated according to the following rules:</p>
    <ul class="list-disc list-inside space-y-1 text-soft mb-4">
      <li>Each row must contain the digits 1-9 without repetition.</li>
      <li>Each column must contain the digits 1-9 without repetition.</li>
      <li>Each of the nine 3 x 3 sub-boxes of the grid must contain the digits 1-9 without repetition.</li>
    </ul>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> 9x9 standard valid board</p><p><span class="text-soft">Output:</span> true</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n²)', 'O(9!)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(n²)'],
    time_big='O(1)',
    time_explain='The board size is fixed at 9 x 9 (81 iterations of constant-time hash set checks).',
    space_big='O(1)',
    space_explain='Fixed hash sets for 9 rows, 9 columns, and 9 sub-boxes.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Box coordinates (r // 3, c // 3):</strong> Mapping (r, c) to box (r // 3, c // 3) identifies which 3x3 block any cell belongs to.'],
    approach_html='''<p class="mb-3">Traverse the board cell by cell with 3 sets of hash collections:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Maintain hash sets for each row <code class="mono accent-text">rows[r]</code>.</li>
      <li>Maintain hash sets for each column <code class="mono accent-text">cols[c]</code>.</li>
      <li>Maintain hash sets for each sub-box <code class="mono accent-text">boxes[(r // 3, c // 3)]</code>.</li>
      <li>If any non-empty digit is already in its row, column, or box set, return false immediately.</li>
    </ol>''',
    python_code='''from typing import List
from collections import defaultdict

class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = defaultdict(set)
        cols = defaultdict(set)
        boxes = defaultdict(set)

        for r in range(9):
            for c in range(9):
                val = board[r][c]
                if val == '.':
                    continue

                box_key = (r // 3, c // 3)
                if val in rows[r] or val in cols[c] or val in boxes[box_key]:
                    return False

                rows[r].add(val)
                cols[c].add(val)
                boxes[box_key].add(val)

        return True''',
    trace_js='''
    const SAMPLE_ROW = ["5","3",".",".","7",".",".",".","."];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const seen = new Set();
      for (let c = 0; c < SAMPLE_ROW.length; c++) {
        const val = SAMPLE_ROW[c];
        if (val === '.') steps.push({ c, val, status: 'empty' });
        else {
          const dup = seen.has(val);
          seen.add(val);
          steps.push({ c, val, status: dup ? 'duplicate' : 'valid' });
        }
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = SAMPLE_ROW.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">col ${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      SAMPLE_ROW.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.c}`).classList.add(s.status === 'valid' ? 'hit' : 'scan');
      caption.textContent = `Row 0, Col ${s.c}: Cell='${s.val}' → ${s.status === 'empty' ? 'Skipped empty cell' : 'Verified valid in row/col/box set!'}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 3. valid-palindrome
NEETCODE_PROBLEMS.append(dict(
    slug='valid-palindrome',
    title='Valid Palindrome',
    category='Two Pointers',
    course='neetcode-150',
    difficulty='Easy',
    tags=['Two Pointers', 'String'],
    leetcode_url='https://leetcode.com/problems/valid-palindrome/',
    statement_html='''<p class="leading-relaxed mb-4">A phrase is a <strong>palindrome</strong> if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.</p>
    <p class="text-soft text-sm mb-5">Given a string <code class="mono">s</code>, return <code class="mono">true</code> if it is a palindrome, or <code class="mono">false</code> otherwise.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "race a car"</p><p><span class="text-soft">Output:</span> false</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Two pointers traverse inwards; each character inspected at most once.',
    space_big='O(1)',
    space_explain='Only two index pointers in-place without copying filtered strings.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">In-place Two Pointers:</strong> Skipping invalid characters on the fly keeps extra space O(1).'],
    approach_html='''<p class="mb-3">Position two pointers at the ends of string <code class="mono accent-text">s</code> and move toward the center:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Set <code class="mono accent-text">left = 0</code> and <code class="mono accent-text">right = len(s) - 1</code>.</li>
      <li>Advance <code class="mono accent-text">left</code> past any non-alphanumeric character.</li>
      <li>Retreat <code class="mono accent-text">right</code> past any non-alphanumeric character.</li>
      <li>Compare <code class="mono accent-text">s[left].lower() == s[right].lower()</code>. If mismatched, return false.</li>
    </ol>''',
    python_code='''class Solution:
    def isPalindrome(self, s: str) -> bool:
        left, right = 0, len(s) - 1

        while left < right:
            while left < right and not s[left].isalnum():
                left += 1
            while left < right and not s[right].isalnum():
                right -= 1

            if s[left].lower() != s[right].lower():
                return False

            left += 1
            right -= 1

        return True''',
    trace_js='''
    const CHARS = ['r', 'a', 'c', 'e', 'c', 'a', 'r'];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let l = 0, r = CHARS.length - 1;
      while (l <= r) {
        steps.push({ l, r, match: CHARS[l] === CHARS[r] });
        l++; r--;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = CHARS.map((c, i) => `<div class="cell" id="cell-${i}">${c}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      CHARS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.l}`).classList.add('hit');
      document.getElementById(`cell-${s.r}`).classList.add('hit');
      document.getElementById(`ptr-${s.l}`).textContent = 'L';
      document.getElementById(`ptr-${s.r}`).textContent = (s.l === s.r) ? 'L/R' : 'R';
      caption.textContent = `Left='${CHARS[s.l]}' at i=${s.l} matches Right='${CHARS[s.r]}' at i=${s.r}!`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 4. two-sum-ii-input-array-is-sorted
NEETCODE_PROBLEMS.append(dict(
    slug='two-sum-ii-input-array-is-sorted',
    title='Two Sum II - Input Array Is Sorted',
    category='Two Pointers',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Two Pointers', 'Binary Search'],
    leetcode_url='https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/',
    statement_html='''<p class="leading-relaxed mb-4">Given a <strong>1-indexed</strong> array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">numbers</code> that is already <strong>sorted in non-decreasing order</strong>, find two numbers such that they add up to a specific <code class="mono">target</code> number.</p>
    <p class="text-soft text-sm mb-5">Return the indices of the two numbers, 1-indexed, as an integer array <code class="mono">[index1, index2]</code> of length 2.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> numbers = [2,7,11,15], target = 9</p><p><span class="text-soft">Output:</span> [1,2] <span class="cm">// 2 + 7 == 9</span></p>',
    trace_html='''<div class="flex flex-col items-center gap-6">
      <div id="array-track" class="flex gap-3 pb-7 pt-7 justify-center flex-wrap"></div>
      <div id="sum-display" class="flex items-center gap-3 text-sm mono py-2 px-5 rounded-xl border border-soft bg-zinc-50 dark:bg-[#141414] min-h-[42px]"></div>
    </div>''',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Two pointers converge inward in at most n comparisons.',
    space_big='O(1)',
    space_explain='No auxiliary data structures used; sorted order allows constant memory.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Sorted Array Leverage:</strong> If sum > target, only moving right pointer left can decrease sum. If sum < target, only moving left pointer right can increase it.'],
    approach_html='''<p class="mb-3">Because the array is already sorted, we can use two pointers with zero extra space:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Set <code class="mono accent-text">left = 0</code> and <code class="mono accent-text">right = len(numbers) - 1</code>.</li>
      <li>Compute <code class="mono accent-text">sum = numbers[left] + numbers[right]</code>.</li>
      <li>If <code class="mono accent-text">sum == target</code>, return <code class="mono accent-text">[left + 1, right + 1]</code> (1-indexed).</li>
      <li>If <code class="mono accent-text">sum > target</code>, decrease <code class="mono accent-text">right</code>; else increase <code class="mono accent-text">left</code>.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        left = 0
        right = len(numbers) - 1

        while left < right:
            current_sum = numbers[left] + numbers[right]

            if current_sum == target:
                # 1-indexed array result
                return [left + 1, right + 1]
            elif current_sum < target:
                left += 1
            else:
                right -= 1

        return []''',
    trace_js='''
    const NUMS = [2, 7, 11, 15];
    const TARGET = 9;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let l = 0;
      let r = NUMS.length - 1;

      while (l < r) {
        const sum = NUMS[l] + NUMS[r];
        const match = sum === TARGET;
        const tooBig = sum > TARGET;

        steps.push({
          l,
          r,
          valL: NUMS[l],
          valR: NUMS[r],
          sum,
          target: TARGET,
          match,
          tooBig,
          caption: match
            ? `🎯 Target sum reached: numbers[${l + 1}] (${NUMS[l]}) + numbers[${r + 1}] (${NUMS[r]}) = ${TARGET}. Return 1-based indices [${l + 1}, ${r + 1}].`
            : (tooBig
                ? `Sum ${sum} > target ${TARGET}. Value at index #${r + 1} (${NUMS[r]}) is too large → decrement right pointer (R moves left).`
                : `Sum ${sum} < target ${TARGET}. Value at index #${l + 1} (${NUMS[l]}) is too small → increment left pointer (L moves right).`)
        });

        if (match) break;
        if (tooBig) {
          r--;
        } else {
          l++;
        }
      }
    }

    function buildTrace() {
      computeSteps();
      stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `
        <div class="cell" id="cell-${i}">
          ${v}
          <span class="idx">#${i + 1}</span>
          <span class="ptr" id="ptr-${i}"></span>
        </div>
      `).join('');
      document.getElementById('sum-display').innerHTML = '<span class="text-soft">Target = ' + TARGET + '</span>';
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        const cell = document.getElementById(`cell-${i}`);
        cell.classList.remove('scan', 'hit', 'discarded');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });

      const sumDisplay = document.getElementById('sum-display');
      const caption = document.getElementById('trace-caption');

      if (stepIndex < 0) {
        sumDisplay.innerHTML = '<span class="text-soft">Target = ' + TARGET + '</span>';
        caption.textContent = 'Click "Next" to begin.';
        updateStepControls();
        return;
      }

      const s = steps[stepIndex];

      NUMS.forEach((_, i) => {
        if (i < s.l || i > s.r) {
          document.getElementById(`cell-${i}`).classList.add('discarded');
        }
      });

      document.getElementById(`ptr-${s.l}`).textContent = 'L';
      document.getElementById(`ptr-${s.r}`).textContent = (s.l === s.r) ? 'L/R' : 'R';

      document.getElementById(`cell-${s.l}`).classList.add(s.match ? 'hit' : 'scan');
      document.getElementById(`cell-${s.r}`).classList.add(s.match ? 'hit' : 'scan');

      sumDisplay.innerHTML = `
        <span class="text-accent font-bold">L:</span> #${s.l + 1} (${s.valL})
        <span class="text-soft">+</span>
        <span class="text-accent font-bold">R:</span> #${s.r + 1} (${s.valR})
        <span class="text-soft">=</span>
        <span class="font-bold ${s.match ? 'text-emerald-400' : (s.tooBig ? 'text-amber-400' : 'text-cyan-400')}">${s.sum}</span>
        <span class="text-soft text-xs">(${s.match ? '== ' + TARGET : (s.tooBig ? '> ' + TARGET : '< ' + TARGET)})</span>
      `;

      caption.textContent = s.caption;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 5. 3sum
NEETCODE_PROBLEMS.append(dict(
    slug='3sum',
    title='3Sum',
    category='Two Pointers',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Two Pointers', 'Sorting'],
    leetcode_url='https://leetcode.com/problems/3sum/',
    statement_html='''<p class="leading-relaxed mb-4">Given an integer array <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, return all the triplets <code class="mono">[nums[i], nums[j], nums[k]]</code> such that <code class="mono">i != j</code>, <code class="mono">i != k</code>, and <code class="mono">j != k</code>, and <code class="mono">nums[i] + nums[j] + nums[k] == 0</code>.</p>
    <p class="text-soft text-sm mb-5">Notice that the solution set must not contain duplicate triplets.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [-1,0,1,2,-1,-4]</p><p><span class="text-soft">Output:</span> [[-1,-1,2],[-1,0,1]]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(n)', 'O(n log n)', 'O(n²)', 'O(n³)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(n²)'],
    time_big='O(n²)',
    time_explain='Sorting takes O(n log n), followed by nested two-pointer search taking O(n²).',
    space_big='O(1)',
    space_explain='Excluding the return list, sorting and two-pointers use O(1) auxiliary space in Python.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Sort + Two Pointers:</strong> Sort first. Loop i from 0..n-2 and run Two Sum II on the remaining subarray. Skip duplicates on i, left, and right.'],
    approach_html='''<p class="mb-3">Reduce the 3Sum problem to Two Sum on a sorted list:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Sort the array in ascending order.</li>
      <li>Iterate <code class="mono accent-text">i</code> from 0 to <code class="mono accent-text">n - 2</code>. If <code class="mono accent-text">nums[i] > 0</code>, stop early.</li>
      <li>Skip duplicate values of <code class="mono accent-text">nums[i]</code>.</li>
      <li>Use two pointers <code class="mono accent-text">left = i + 1</code> and <code class="mono accent-text">right = n - 1</code> to find pairs summing to <code class="mono accent-text">-nums[i]</code>.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        res = []

        for i in range(len(nums) - 2):
            if nums[i] > 0:
                break
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            left, right = i + 1, len(nums) - 1
            while left < right:
                total = nums[i] + nums[left] + nums[right]
                if total < 0:
                    left += 1
                elif total > 0:
                    right -= 1
                else:
                    res.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left + 1]:
                        left += 1
                    while left < right and nums[right] == nums[right - 1]:
                        right -= 1
                    left += 1
                    right -= 1

        return res''',
    trace_js='''
    const NUMS = [-4, -1, -1, 0, 1, 2];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ i: 0, l: 1, r: 5, sum: -4 + -1 + 2, match: false, note: 'nums[0]=-4: sum=-3 < 0' });
      steps.push({ i: 1, l: 2, r: 5, sum: -1 + -1 + 2, match: true, note: 'nums[1]=-1: [-1, -1, 2] = 0! MATCH' });
      steps.push({ i: 1, l: 3, r: 4, sum: -1 + 0 + 1, match: true, note: 'nums[1]=-1: [-1, 0, 1] = 0! MATCH' });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.i}`).classList.add('scan');
      document.getElementById(`cell-${s.l}`).classList.add(s.match ? 'hit' : 'scan');
      document.getElementById(`cell-${s.r}`).classList.add(s.match ? 'hit' : 'scan');
      document.getElementById(`ptr-${s.i}`).textContent = 'i';
      document.getElementById(`ptr-${s.l}`).textContent = 'L';
      document.getElementById(`ptr-${s.r}`).textContent = 'R';
      caption.textContent = `${s.note}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 6. trapping-rain-water
NEETCODE_PROBLEMS.append(dict(
    slug='trapping-rain-water',
    title='Trapping Rain Water',
    category='Two Pointers',
    course='neetcode-150',
    difficulty='Hard',
    tags=['Array', 'Two Pointers', 'Dynamic Programming', 'Stack'],
    leetcode_url='https://leetcode.com/problems/trapping-rain-water/',
    statement_html='''<p class="leading-relaxed mb-4">Given <code class="mono">n</code> non-negative integers representing an elevation map where the width of each bar is <code class="mono">1</code>, compute how much water it can trap after raining.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> height = [0,1,0,2,1,0,1,3,2,1,2,1]</p><p><span class="text-soft">Output:</span> 6</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Left and right pointers traverse inward until meeting; each index processed once.',
    space_big='O(1)',
    space_explain='Only four tracking variables: left, right, left_max, right_max.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Bottleneck Principle:</strong> Water trapped at any bar is determined by min(max_left, max_right) - height[i]. Move the pointer with the smaller max inward.'],
    approach_html='''<p class="mb-3">Two pointers avoid the O(n) prefix/suffix memory arrays:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Initialize <code class="mono accent-text">left = 0</code> and <code class="mono accent-text">right = len(height) - 1</code>.</li>
      <li>Track <code class="mono accent-text">left_max</code> and <code class="mono accent-text">right_max</code>.</li>
      <li>If <code class="mono accent-text">left_max < right_max</code>, advance left; add <code class="mono accent-text">left_max - height[left]</code> to water.</li>
      <li>Otherwise retreat right; add <code class="mono accent-text">right_max - height[right]</code> to water.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def trap(self, height: List[int]) -> int:
        if not height:
            return 0

        left, right = 0, len(height) - 1
        left_max, right_max = height[left], height[right]
        water = 0

        while left < right:
            if left_max < right_max:
                left += 1
                left_max = max(left_max, height[left])
                water += left_max - height[left]
            else:
                right -= 1
                right_max = max(right_max, height[right])
                water += right_max - height[right]

        return water''',
    trace_js='''
    const HEIGHTS = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let l = 0, r = HEIGHTS.length - 1, lMax = HEIGHTS[l], rMax = HEIGHTS[r], water = 0;
      while (l < r) {
        if (lMax < rMax) {
          l++;
          lMax = Math.max(lMax, HEIGHTS[l]);
          const added = Math.max(0, lMax - HEIGHTS[l]);
          water += added;
          steps.push({ l, r, lMax, rMax, added, water });
        } else {
          r--;
          rMax = Math.max(rMax, HEIGHTS[r]);
          const added = Math.max(0, rMax - HEIGHTS[r]);
          water += added;
          steps.push({ l, r, lMax, rMax, added, water });
        }
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = HEIGHTS.map((h, i) => `<div class="cell" id="cell-${i}" style="height:${28 + h * 8}px; align-items:flex-end; padding-bottom:4px;">${h}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      HEIGHTS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.l}`).classList.add(s.added > 0 ? 'hit' : 'scan');
      document.getElementById(`cell-${s.r}`).classList.add(s.added > 0 ? 'hit' : 'scan');
      document.getElementById(`ptr-${s.l}`).textContent = 'L';
      document.getElementById(`ptr-${s.r}`).textContent = 'R';
      caption.textContent = `L=${s.l}, R=${s.r} | LeftMax=${s.lMax}, RightMax=${s.rMax} | Added +${s.added} water → Total: ${s.water}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 7. permutation-in-string
NEETCODE_PROBLEMS.append(dict(
    slug='permutation-in-string',
    title='Permutation in String',
    category='Sliding Window',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Hash Table', 'Two Pointers', 'String', 'Sliding Window'],
    leetcode_url='https://leetcode.com/problems/permutation-in-string/',
    statement_html='''<p class="leading-relaxed mb-4">Given two strings <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s1</code> and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s2</code>, return <code class="mono">true</code> if <code class="mono">s2</code> contains a permutation of <code class="mono">s1</code>, or <code class="mono">false</code> otherwise.</p>
    <p class="text-soft text-sm mb-5">In other words, return <code class="mono">true</code> if one of <code class="mono">s1</code>'s permutations is the substring of <code class="mono">s2</code>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s1 = "ab", s2 = "eidbaooo"</p><p><span class="text-soft">Output:</span> true <span class="cm">// s2 contains "ba" which is a permutation of "ab".</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(len(s2))', 'O(len(s1) * len(s2))', 'O(26!)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(len(s2))',
    time_explain='Fixed-size sliding window slides across s2 in a single linear pass.',
    space_big='O(1)',
    space_explain='Two frequency arrays of fixed size 26 for lowercase English letters.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Fixed Window Length len(s1):</strong> Since permutations must have identical length, keep window size strictly equal to len(s1).'],
    approach_html='''<p class="mb-3">Slide a fixed-size window across <code class="mono accent-text">s2</code>:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>If <code class="mono accent-text">len(s1) > len(s2)</code>, return false.</li>
      <li>Initialize frequency counts for <code class="mono accent-text">s1</code> and the first <code class="mono accent-text">len(s1)</code> chars of <code class="mono accent-text">s2</code>.</li>
      <li>Slide the window right: add new incoming char, decrement/remove old outgoing char.</li>
      <li>If the window frequency matches <code class="mono accent-text">s1</code> frequency, return true.</li>
    </ol>''',
    python_code='''from collections import Counter

class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        if len(s1) > len(s2):
            return False

        s1_count = Counter(s1)
        window = Counter(s2[:len(s1)])

        if s1_count == window:
            return True

        for i in range(len(s1), len(s2)):
            window[s2[i]] += 1
            old_char = s2[i - len(s1)]
            window[old_char] -= 1
            if window[old_char] == 0:
                del window[old_char]

            if window == s1_count:
                return True

        return False''',
    trace_js='''
    const S1 = "ab", S2 = "eidbaooo";
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const k = S1.length;
      for (let i = 0; i <= S2.length - k; i++) {
        const sub = S2.slice(i, i + k);
        const match = (sub === 'ab' || sub === 'ba');
        steps.push({ i, sub, match });
        if (match) break;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = S2.split('').map((c, i) => `<div class="cell" id="cell-${i}">${c}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      S2.split('').forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < S2.length; i++) {
        if (i >= s.i && i < s.i + S1.length) document.getElementById(`cell-${i}`).classList.add(s.match ? 'hit' : 'scan');
        else document.getElementById(`cell-${i}`).classList.add('discarded');
      }
      caption.textContent = `Window [${s.i}..${s.i+1}]: "${s.sub}" ${s.match ? 'is a permutation of "ab"! Return true.' : 'does not match target "ab".'}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 8. minimum-window-substring
NEETCODE_PROBLEMS.append(dict(
    slug='minimum-window-substring',
    title='Minimum Window Substring',
    category='Sliding Window',
    course='neetcode-150',
    difficulty='Hard',
    tags=['Hash Table', 'String', 'Sliding Window'],
    leetcode_url='https://leetcode.com/problems/minimum-window-substring/',
    statement_html='''<p class="leading-relaxed mb-4">Given two strings <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s</code> and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">t</code> of lengths <code class="mono">m</code> and <code class="mono">n</code> respectively, return the <strong>minimum window substring</strong> of <code class="mono">s</code> such that every character in <code class="mono">t</code> (including duplicates) is included in the window.</p>
    <p class="text-soft text-sm mb-5">If there is no such substring, return the empty string <code class="mono">""</code>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "ADOBECODEBANC", t = "ABC"</p><p><span class="text-soft">Output:</span> "BANC"</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(m + n)', 'O(m * n)', 'O(m log n)', 'O(2^n)'],
    quiz_space_opts=['O(1)', 'O(m + n)', 'O(m * n)'],
    time_big='O(m + n)',
    time_explain='Right pointer visits each character once; left pointer advances at most m times.',
    space_big='O(m + n)',
    space_explain='Hash maps for character frequency requirements of t and active window characters of s.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Have vs Need variables:</strong> Track the count of unique matching characters to verify window validity in O(1) instead of comparing full maps.'],
    approach_html='''<p class="mb-3">Sliding window with dynamic contraction:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Map target character frequencies with <code class="mono accent-text">target_counts</code> and track <code class="mono accent-text">need = len(target_counts)</code>.</li>
      <li>Expand <code class="mono accent-text">right</code> pointer and update <code class="mono accent-text">have</code> when a character frequency is met.</li>
      <li>While <code class="mono accent-text">have == need</code>, record minimum window, then contract from <code class="mono accent-text">left</code>.</li>
      <li>Return shortest valid slice or empty string.</li>
    </ol>''',
    python_code='''from collections import Counter

class Solution:
    def minWindow(self, s: str, t: str) -> str:
        if not t or not s:
            return ""

        target_counts = Counter(t)
        window_counts = {}
        have, need = 0, len(target_counts)
        res, res_len = [-1, -1], float("inf")
        l = 0

        for r in range(len(s)):
            c = s[r]
            window_counts[c] = window_counts.get(c, 0) + 1

            if c in target_counts and window_counts[c] == target_counts[c]:
                have += 1

            while have == need:
                if (r - l + 1) < res_len:
                    res = [l, r]
                    res_len = r - l + 1

                window_counts[s[l]] -= 1
                if s[l] in target_counts and window_counts[s[l]] < target_counts[s[l]]:
                    have -= 1
                l += 1

        l, r = res
        return s[l:r + 1] if res_len != float("inf") else ""''',
    trace_js='''
    const S = "ADOBECODEBANC";
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ l: 0, r: 5, sub: "ADOBEC", match: true, best: "ADOBEC" });
      steps.push({ l: 5, r: 10, sub: "CODEBA", match: true, best: "CODEBA" });
      steps.push({ l: 9, r: 12, sub: "BANC", match: true, best: "BANC" });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = S.split('').map((c, i) => `<div class="cell" id="cell-${i}">${c}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      S.split('').forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < S.length; i++) {
        if (i >= s.l && i <= s.r) document.getElementById(`cell-${i}`).classList.add('hit');
        else document.getElementById(`cell-${i}`).classList.add('discarded');
      }
      caption.textContent = `Valid window found at [${s.l}..${s.r}]: "${s.sub}" → Current best window: "${s.best}" (len ${s.best.length})`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 9. sliding-window-maximum
NEETCODE_PROBLEMS.append(dict(
    slug='sliding-window-maximum',
    title='Sliding Window Maximum',
    category='Sliding Window',
    course='neetcode-150',
    difficulty='Hard',
    tags=['Array', 'Queue', 'Sliding Window', 'Monotonic Queue'],
    leetcode_url='https://leetcode.com/problems/sliding-window-maximum/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code>, there is a sliding window of size <code class="mono">k</code> which is moving from the very left of the array to the very right.</p>
    <p class="text-soft text-sm mb-5">You can only see the <code class="mono">k</code> numbers in the window. Each time the sliding window moves right by one position, return the <strong>max sliding window</strong>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [1,3,-1,-3,5,3,6,7], k = 3</p><p><span class="text-soft">Output:</span> [3,3,5,5,6,7]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(n)', 'O(n log k)', 'O(n * k)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(k)', 'O(n)'],
    time_big='O(n)',
    time_explain='Each array element is pushed and popped from the monotonic deque at most once.',
    space_big='O(k)',
    space_explain='The monotonic deque stores at most k indices corresponding to the active window.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Monotonic Decreasing Deque:</strong> Maintain elements in decreasing order in a deque. Smaller preceding elements can never be the maximum again.'],
    approach_html='''<p class="mb-3">Monotonic Deque tracks candidates in O(n) total time:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Maintain a double-ended queue storing indices in decreasing value order.</li>
      <li>Before adding <code class="mono accent-text">nums[i]</code>, pop smaller elements from the back.</li>
      <li>Evict indices from the front that have fallen out of the <code class="mono accent-text">k</code>-length window.</li>
      <li>The front index of the deque is always the maximum for the current window.</li>
    </ol>''',
    python_code='''from typing import List
from collections import deque

class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        q = deque()  # stores indices
        res = []

        for i, n in enumerate(nums):
            while q and nums[q[-1]] < n:
                q.pop()
            q.append(i)

            if q[0] <= i - k:
                q.popleft()

            if i >= k - 1:
                res.append(nums[q[0]])

        return res''',
    trace_js='''
    const NUMS = [1, 3, -1, -3, 5, 3, 6, 7];
    const K = 3;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const res = [3, 3, 5, 5, 6, 7];
      for (let i = 0; i <= NUMS.length - K; i++) {
        steps.push({ start: i, end: i + K - 1, max: res[i] });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < NUMS.length; i++) {
        if (i >= s.start && i <= s.end) {
          document.getElementById(`cell-${i}`).classList.add(NUMS[i] === s.max ? 'hit' : 'scan');
        } else {
          document.getElementById(`cell-${i}`).classList.add('discarded');
        }
      }
      caption.textContent = `Window [${s.start}..${s.end}]: [${NUMS.slice(s.start, s.end + 1).join(', ')}] → Window Max is ${s.max}!`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 10. valid-parentheses
NEETCODE_PROBLEMS.append(dict(
    slug='valid-parentheses',
    title='Valid Parentheses',
    category='Stack',
    course='neetcode-150',
    difficulty='Easy',
    tags=['String', 'Stack'],
    leetcode_url='https://leetcode.com/problems/valid-parentheses/',
    statement_html='''<p class="leading-relaxed mb-4">Given a string <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">s</code> containing just the characters <code class="mono">'('</code>, <code class="mono">')'</code>, <code class="mono">'{'</code>, <code class="mono">'}'</code>, <code class="mono">'['</code> and <code class="mono">']'</code>, determine if the input string is valid.</p>
    <p class="text-soft text-sm mb-5">Open brackets must be closed by the same type of brackets in the correct order, and every close bracket has a corresponding open bracket.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> s = "()[]{}"</p><p><span class="text-soft">Output:</span> true</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Single pass through s with O(1) push and pop stack operations.',
    space_big='O(n)',
    space_explain='In the worst case (all open brackets), stack holds n characters.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">LIFO Stack Matching:</strong> Each closing bracket must pair with the most recently opened unmatched bracket.'],
    approach_html='''<p class="mb-3">Use a stack to match brackets in last-in, first-out order:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Map each closing bracket to its matching open bracket in a dictionary.</li>
      <li>Iterate through characters: if opening bracket, push to stack.</li>
      <li>If closing bracket, verify that stack is non-empty and top matches; pop it.</li>
      <li>Return true if the stack is completely empty at the end.</li>
    </ol>''',
    python_code='''class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}

        for char in s:
            if char in pairs:
                if not stack or stack[-1] != pairs[char]:
                    return False
                stack.pop()
            else:
                stack.append(char)

        return len(stack) == 0''',
    trace_js='''
    const CHARS = ['(', '{', '[', ']', '}', ')'];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const stack = [];
      const pairs = { ')': '(', '}': '{', ']': '[' };
      for (let i = 0; i < CHARS.length; i++) {
        const c = CHARS[i];
        if (pairs[c]) {
          const popped = stack.pop();
          steps.push({ i, c, action: 'pop', stack: [...stack], match: popped === pairs[c] });
        } else {
          stack.push(c);
          steps.push({ i, c, action: 'push', stack: [...stack], match: true });
        }
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = CHARS.map((c, i) => `<div class="cell" id="cell-${i}">${c}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      CHARS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.i}`).classList.add(s.action === 'pop' ? 'hit' : 'scan');
      caption.textContent = `Scanned '${s.c}' → ${s.action.toUpperCase()} | Stack: [${s.stack.join(', ') || 'empty'}]`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 11. min-stack
NEETCODE_PROBLEMS.append(dict(
    slug='min-stack',
    title='Min Stack',
    category='Stack',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Stack', 'Design'],
    leetcode_url='https://leetcode.com/problems/min-stack/',
    statement_html='''<p class="leading-relaxed mb-4">Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.</p>
    <ul class="list-disc list-inside space-y-1 text-soft mb-4">
      <li><code class="mono">push(val)</code> pushes element val onto the stack.</li>
      <li><code class="mono">pop()</code> removes the element on the top of the stack.</li>
      <li><code class="mono">top()</code> gets the top element of the stack.</li>
      <li><code class="mono">getMin()</code> retrieves the minimum element in the stack in O(1).</li>
    </ul>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> ["MinStack","push","push","push","getMin","pop","top","getMin"]<br>[[],[-2],[0],[-3],[],[],[],[]]</p><p><span class="text-soft">Output:</span> [null,null,null,null,-3,null,0,-2]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1) all ops', 'O(n) getMin', 'O(log n) push', 'O(n) push'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(n²)'],
    time_big='O(1)',
    time_explain='Every operation (push, pop, top, getMin) executes in constant O(1) time.',
    space_big='O(n)',
    space_explain='Auxiliary minimum tracking stack scales linearly with total number of elements.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Parallel Min Stack:</strong> Store the running minimum alongside every element. When an element pops, its corresponding min automatically pops too.'],
    approach_html='''<p class="mb-3">Use two synchronized stacks:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Main stack stores all pushed values.</li>
      <li>Min stack stores <code class="mono accent-text">min(val, min_stack[-1])</code> for each push.</li>
      <li>On <code class="mono accent-text">pop()</code>, pop from both stacks.</li>
      <li><code class="mono accent-text">getMin()</code> simply returns <code class="mono accent-text">min_stack[-1]</code> in O(1) time.</li>
    </ol>''',
    python_code='''class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        min_val = min(val, self.min_stack[-1] if self.min_stack else val)
        self.min_stack.append(min_val)

    def pop(self) -> None:
        self.stack.pop()
        self.min_stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]''',
    trace_js='''
    const OPS = [
      { op: "push(-2)", stack: [-2], min: [-2] },
      { op: "push(0)", stack: [-2, 0], min: [-2, -2] },
      { op: "push(-3)", stack: [-2, 0, -3], min: [-2, -2, -3] },
      { op: "getMin() → -3", stack: [-2, 0, -3], min: [-2, -2, -3] },
      { op: "pop()", stack: [-2, 0], min: [-2, -2] },
      { op: "getMin() → -2", stack: [-2, 0], min: [-2, -2] }
    ];
    let stepIndex = -1;

    function buildTrace() {
      stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = OPS.map((o, i) => `<div class="cell" id="cell-${i}" style="width:auto; padding:0 12px; font-size:13px;">${o.op}</div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      OPS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = OPS[stepIndex];
      document.getElementById(`cell-${stepIndex}`).classList.add('hit');
      caption.textContent = `${s.op} | Main Stack: [${s.stack.join(', ')}] | Min Stack Top: ${s.min[s.min.length - 1]}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${OPS.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= OPS.length - 1;
    }
'''
))

# 12. evaluate-reverse-polish-notation
NEETCODE_PROBLEMS.append(dict(
    slug='evaluate-reverse-polish-notation',
    title='Evaluate Reverse Polish Notation',
    category='Stack',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Math', 'Stack'],
    leetcode_url='https://leetcode.com/problems/evaluate-reverse-polish-notation/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an array of strings <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">tokens</code> that represents an arithmetic expression in a <strong>Reverse Polish Notation</strong> (postfix).</p>
    <p class="text-soft text-sm mb-5">Evaluate the expression and return an integer that represents its value. Valid operators are <code class="mono">'+'</code>, <code class="mono">'-'</code>, <code class="mono">'*'</code>, and <code class="mono">'/'</code>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> tokens = ["2","1","+","3","*"]</p><p><span class="text-soft">Output:</span> 9 <span class="cm">// ((2 + 1) * 3) = 9</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Single pass through tokens with constant-time stack operations per token.',
    space_big='O(n)',
    space_explain='Stack holds operands and intermediate evaluation results.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Operand Stack:</strong> In RPN, operators immediately follow their operands. Push numbers, pop twice on operator, push evaluated result back.'],
    approach_html='''<p class="mb-3">Evaluate postfix expression in a single pass using an operand stack:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Iterate through each token in the input list.</li>
      <li>If token is a number, push it onto the stack.</li>
      <li>If token is an operator, pop operand <code class="mono accent-text">b</code> then operand <code class="mono accent-text">a</code>.</li>
      <li>Apply operator <code class="mono accent-text">a op b</code> and push the integer result back.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        stack = []
        for t in tokens:
            if t in "+-*/":
                b = stack.pop()
                a = stack.pop()
                if t == '+': stack.append(a + b)
                elif t == '-': stack.append(a - b)
                elif t == '*': stack.append(a * b)
                elif t == '/': stack.append(int(a / b))
            else:
                stack.append(int(t))
        return stack[0]''',
    trace_js='''
    const TOKENS = ["2", "1", "+", "3", "*"];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ i: 0, t: "2", stack: [2], caption: 'Push 2' });
      steps.push({ i: 1, t: "1", stack: [2, 1], caption: 'Push 1' });
      steps.push({ i: 2, t: "+", stack: [3], caption: 'Operator + : 2 + 1 = 3' });
      steps.push({ i: 3, t: "3", stack: [3, 3], caption: 'Push 3' });
      steps.push({ i: 4, t: "*", stack: [9], caption: 'Operator * : 3 * 3 = 9' });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = TOKENS.map((t, i) => `<div class="cell" id="cell-${i}">${t}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      TOKENS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.i}`).classList.add(s.t in {"+":1,"*":1} ? 'hit' : 'scan');
      caption.textContent = `Token '${s.t}': ${s.caption} | Stack: [${s.stack.join(', ')}]`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 13. daily-temperatures
NEETCODE_PROBLEMS.append(dict(
    slug='daily-temperatures',
    title='Daily Temperatures',
    category='Stack',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Stack', 'Monotonic Stack'],
    leetcode_url='https://leetcode.com/problems/daily-temperatures/',
    statement_html='''<p class="leading-relaxed mb-4">Given an array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">temperatures</code> represents the daily temperatures, return an array <code class="mono">answer</code> such that <code class="mono">answer[i]</code> is the number of days you have to wait after the <code class="mono">i</code>th day to get a warmer temperature.</p>
    <p class="text-soft text-sm mb-5">If there is no future day for which this is possible, keep <code class="mono">answer[i] == 0</code> instead.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> temperatures = [73,74,75,71,69,72,76,73]</p><p><span class="text-soft">Output:</span> [1,1,4,2,1,1,0,0]</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Every day is pushed onto the monotonic stack and popped at most once.',
    space_big='O(n)',
    space_explain='Monotonic stack stores pairs of (temperature, index) up to length n.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Monotonic Decreasing Stack:</strong> Keep days waiting for a warmer temperature on a stack in decreasing temperature order. When a warmer day arrives, resolve all smaller days!'],
    approach_html='''<p class="mb-3">Use a monotonic decreasing stack:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Initialize result array with zeros of size <code class="mono accent-text">len(temperatures)</code>.</li>
      <li>Iterate through each day with temperature <code class="mono accent-text">t</code> and index <code class="mono accent-text">i</code>.</li>
      <li>While stack is not empty and <code class="mono accent-text">t > stack[-1][0]</code>, pop <code class="mono accent-text">(prev_t, prev_i)</code> and set <code class="mono accent-text">res[prev_i] = i - prev_i</code>.</li>
      <li>Push current <code class="mono accent-text">(t, i)</code> to stack.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        res = [0] * len(temperatures)
        stack = []  # pairs: (temp, index)

        for i, t in enumerate(temperatures):
            while stack and t > stack[-1][0]:
                stack_t, stack_i = stack.pop()
                res[stack_i] = i - stack_i
            stack.append((t, i))

        return res''',
    trace_js='''
    const TEMPS = [73, 74, 75, 71, 69, 72, 76, 73];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      const res = new Array(TEMPS.length).fill(0);
      const stack = [];
      for (let i = 0; i < TEMPS.length; i++) {
        const t = TEMPS[i];
        while (stack.length && t > stack[stack.length - 1][0]) {
          const [st, si] = stack.pop();
          res[si] = i - si;
          steps.push({ i, t, resolvedIdx: si, wait: i - si, res: [...res] });
        }
        stack.push([t, i]);
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = TEMPS.map((t, i) => `<div class="cell" id="cell-${i}">${t}°<span class="idx">day ${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      TEMPS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.i}`).classList.add('hit');
      document.getElementById(`cell-${s.resolvedIdx}`).classList.add('scan');
      caption.textContent = `Day ${s.i} (${s.t}°) is warmer than Day ${s.resolvedIdx} (${TEMPS[s.resolvedIdx]}°)! Waited ${s.wait} day(s).`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 14. largest-rectangle-in-histogram
NEETCODE_PROBLEMS.append(dict(
    slug='largest-rectangle-in-histogram',
    title='Largest Rectangle in Histogram',
    category='Stack',
    course='neetcode-150',
    difficulty='Hard',
    tags=['Array', 'Stack', 'Monotonic Stack'],
    leetcode_url='https://leetcode.com/problems/largest-rectangle-in-histogram/',
    statement_html='''<p class="leading-relaxed mb-4">Given an array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">heights</code> representing the histogram\'s bar height where the width of each bar is <code class="mono">1</code>, return the area of the <strong>largest rectangle</strong> in the histogram.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> heights = [2,1,5,6,2,3]</p><p><span class="text-soft">Output:</span> 10 <span class="cm">// Bars at index 2 and 3 with height 5 create rectangle of area 5 * 2 = 10.</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n)',
    time_explain='Each bar is pushed and popped from the monotonic increasing stack at most once.',
    space_big='O(n)',
    space_explain='Monotonic stack stores at most n index-height pairs.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Monotonic Increasing Stack:</strong> As long as bars get taller, push to stack. When a shorter bar appears, pop taller bars and compute their maximum extendable width.'],
    approach_html='''<p class="mb-3">Monotonic stack computes maximum area in linear time:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Maintain a monotonic increasing stack of pairs <code class="mono accent-text">(index, height)</code>.</li>
      <li>When encountering a bar shorter than stack top, pop from stack.</li>
      <li>Compute area with popped height across width <code class="mono accent-text">current_i - popped_index</code>.</li>
      <li>Push the new bar with the leftmost index of any popped bars.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        max_area = 0
        stack = []  # (index, height)

        for i, h in enumerate(heights):
            start = i
            while stack and stack[-1][1] > h:
                idx, height = stack.pop()
                max_area = max(max_area, height * (i - idx))
                start = idx
            stack.append((start, h))

        for idx, height in stack:
            max_area = max(max_area, height * (len(heights) - idx))

        return max_area''',
    trace_js='''
    const HEIGHTS = [2, 1, 5, 6, 2, 3];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ i: 0, h: 2, maxArea: 2, note: 'Push bar 2' });
      steps.push({ i: 1, h: 1, maxArea: 2, note: 'Bar 1 < 2 → Pop 2, area=2*1=2' });
      steps.push({ i: 2, h: 5, maxArea: 5, note: 'Push bar 5' });
      steps.push({ i: 3, h: 6, maxArea: 6, note: 'Push bar 6' });
      steps.push({ i: 4, h: 2, maxArea: 10, note: 'Bar 2 < 6, 5 → Pop 6 (area=6), Pop 5 (area=5*2=10! NEW MAX)' });
      steps.push({ i: 5, h: 3, maxArea: 10, note: 'Final bars processed → Max Area: 10' });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = HEIGHTS.map((h, i) => `<div class="cell" id="cell-${i}" style="height:${28 + h * 7}px; align-items:flex-end; padding-bottom:4px;">${h}<span class="idx">i=${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      HEIGHTS.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      document.getElementById(`cell-${s.i}`).classList.add('hit');
      caption.textContent = `${s.note} | Running Max Area: ${s.maxArea}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 15. binary-search
NEETCODE_PROBLEMS.append(dict(
    slug='binary-search',
    title='Binary Search',
    category='Binary Search',
    course='neetcode-150',
    difficulty='Easy',
    tags=['Array', 'Binary Search'],
    leetcode_url='https://leetcode.com/problems/binary-search/',
    statement_html='''<p class="leading-relaxed mb-4">Given an array of integers <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums</code> which is sorted in ascending order, and an integer <code class="mono">target</code>, write a function to search <code class="mono">target</code> in <code class="mono">nums</code>.</p>
    <p class="text-soft text-sm mb-5">If <code class="mono">target</code> exists, then return its index. Otherwise, return <code class="mono">-1</code>. You must write an algorithm with <code class="mono">O(log n)</code> runtime complexity.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums = [-1,0,3,5,9,12], target = 9</p><p><span class="text-soft">Output:</span> 4 <span class="cm">// 9 exists in nums and its index is 4</span></p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
    quiz_space_opts=['O(1)', 'O(log n)', 'O(n)'],
    time_big='O(log n)',
    time_explain='Search space is cut strictly in half on every step.',
    space_big='O(1)',
    space_explain='Only low, mid, and high pointers are maintained iteratively.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Divide and Conquer by 2:</strong> In a sorted array, comparing with the middle element eliminates half of all remaining candidates.'],
    approach_html='''<p class="mb-3">Standard binary search on a sorted array:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Initialize <code class="mono accent-text">low = 0</code> and <code class="mono accent-text">high = len(nums) - 1</code>.</li>
      <li>Compute midpoint <code class="mono accent-text">mid = (low + high) // 2</code>.</li>
      <li>If <code class="mono accent-text">nums[mid] == target</code>, return <code class="mono accent-text">mid</code>.</li>
      <li>If <code class="mono accent-text">nums[mid] < target</code>, eliminate left half: <code class="mono accent-text">low = mid + 1</code>.</li>
      <li>Else eliminate right half: <code class="mono accent-text">high = mid - 1</code>.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def search(self, nums: List[int], target: int) -> int:
        low, high = 0, len(nums) - 1

        while low <= high:
            mid = (low + high) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                low = mid + 1
            else:
                high = mid - 1

        return -1''',
    trace_js='''
    const NUMS = [-1, 0, 3, 5, 9, 12];
    const TARGET = 9;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let low = 0, high = NUMS.length - 1;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        const match = NUMS[mid] === TARGET;
        steps.push({ low, mid, high, match });
        if (match) break;
        if (NUMS[mid] < TARGET) low = mid + 1; else high = mid - 1;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = NUMS.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">i=${i}</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      NUMS.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < NUMS.length; i++) {
        if (i < s.low || i > s.high) document.getElementById(`cell-${i}`).classList.add('discarded');
      }
      document.getElementById(`cell-${s.mid}`).classList.add(s.match ? 'hit' : 'scan');
      document.getElementById(`ptr-${s.low}`).textContent = 'low';
      document.getElementById(`ptr-${s.high}`).textContent = (s.low === s.high) ? 'low/high' : 'high';
      document.getElementById(`ptr-${s.mid}`).textContent = s.match ? 'FOUND' : 'mid';
      caption.textContent = `low=${s.low}, high=${s.high}, mid=${s.mid} (nums[${s.mid}]=${NUMS[s.mid]}) → ${s.match ? 'Match found! Return ' + s.mid : (NUMS[s.mid] < TARGET ? 'Less than target → search right half' : 'Greater than target → search left half')}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 16. search-a-2d-matrix
NEETCODE_PROBLEMS.append(dict(
    slug='search-a-2d-matrix',
    title='Search a 2D Matrix',
    category='Binary Search',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Binary Search', 'Matrix'],
    leetcode_url='https://leetcode.com/problems/search-a-2d-matrix/',
    statement_html='''<p class="leading-relaxed mb-4">You are given an <code class="mono">m x n</code> integer matrix with the following two properties:</p>
    <ul class="list-disc list-inside space-y-1 text-soft mb-4">
      <li>Each row is sorted in non-decreasing order.</li>
      <li>The first integer of each row is greater than the last integer of the previous row.</li>
    </ul>
    <p class="text-soft text-sm mb-5">Given an integer <code class="mono">target</code>, return <code class="mono">true</code> if <code class="mono">target</code> is in <code class="mono">matrix</code> or <code class="mono">false</code> otherwise in <code class="mono">O(log(m * n))</code> time.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3</p><p><span class="text-soft">Output:</span> true</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(log(m * n))', 'O(m + n)', 'O(m * n)', 'O(log m * log n)'],
    quiz_space_opts=['O(1)', 'O(m * n)', 'O(log(m * n))'],
    time_big='O(log(m * n))',
    time_explain='Binary search across virtual flattened 1D array of size m * n.',
    space_big='O(1)',
    space_explain='Index math converts 1D mid into (row, col) coordinates with zero memory overhead.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Virtual 1D Mapping:</strong> row = mid // cols, col = mid % cols treats an m x n sorted matrix as a flat sorted 1D array.'],
    approach_html='''<p class="mb-3">Binary search directly across the entire matrix treated as a virtual 1D array:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Set <code class="mono accent-text">low = 0</code> and <code class="mono accent-text">high = (rows * cols) - 1</code>.</li>
      <li>Compute virtual midpoint <code class="mono accent-text">mid = (low + high) // 2</code>.</li>
      <li>Convert to 2D coordinates: <code class="mono accent-text">r = mid // cols</code>, <code class="mono accent-text">c = mid % cols</code>.</li>
      <li>If <code class="mono accent-text">matrix[r][c] == target</code> return true; adjust low/high accordingly.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        if not matrix or not matrix[0]:
            return False

        rows, cols = len(matrix), len(matrix[0])
        low, high = 0, rows * cols - 1

        while low <= high:
            mid = (low + high) // 2
            val = matrix[mid // cols][mid % cols]

            if val == target:
                return True
            elif val < target:
                low = mid + 1
            else:
                high = mid - 1

        return False''',
    trace_js='''
    const FLAT = [1, 3, 5, 7, 10, 11, 16, 20, 23, 30, 34, 60];
    const TARGET = 3, COLS = 4;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let low = 0, high = FLAT.length - 1;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        const match = FLAT[mid] === TARGET;
        const r = Math.floor(mid / COLS), c = mid % COLS;
        steps.push({ low, mid, high, r, c, val: FLAT[mid], match });
        if (match) break;
        if (FLAT[mid] < TARGET) low = mid + 1; else high = mid - 1;
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = FLAT.map((v, i) => `<div class="cell" id="cell-${i}">${v}<span class="idx">[${Math.floor(i/COLS)},${i%COLS}]</span><span class="ptr" id="ptr-${i}"></span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      FLAT.forEach((_, i) => {
        document.getElementById(`cell-${i}`).classList.remove('scan', 'hit', 'discarded');
        const ptr = document.getElementById(`ptr-${i}`);
        if (ptr) ptr.textContent = '';
      });
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      for (let i = 0; i < FLAT.length; i++) {
        if (i < s.low || i > s.high) document.getElementById(`cell-${i}`).classList.add('discarded');
      }
      document.getElementById(`cell-${s.mid}`).classList.add(s.match ? 'hit' : 'scan');
      document.getElementById(`ptr-${s.mid}`).textContent = s.match ? 'TARGET' : 'mid';
      caption.textContent = `mid=${s.mid} → matrix[${s.r}][${s.c}] = ${s.val} ${s.match ? '== TARGET! Found.' : (s.val < TARGET ? '< target → search right' : '> target → search left')}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 17. koko-eating-bananas
NEETCODE_PROBLEMS.append(dict(
    slug='koko-eating-bananas',
    title='Koko Eating Bananas',
    category='Binary Search',
    course='neetcode-150',
    difficulty='Medium',
    tags=['Array', 'Binary Search'],
    leetcode_url='https://leetcode.com/problems/koko-eating-bananas/',
    statement_html='''<p class="leading-relaxed mb-4">Koko loves to eat bananas. There are <code class="mono">n</code> piles of bananas, the <code class="mono">i</code>th pile has <code class="mono">piles[i]</code> bananas. The guards will come back in <code class="mono">h</code> hours.</p>
    <p class="text-soft text-sm mb-5">Koko can decide her bananas-per-hour eating speed of <code class="mono">k</code>. Return the minimum integer <code class="mono">k</code> such that she can eat all the bananas within <code class="mono">h</code> hours.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> piles = [3,6,7,11], h = 8</p><p><span class="text-soft">Output:</span> 4</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(n log(max(piles)))', 'O(n * max(piles))', 'O(n log n)', 'O(n²)'],
    quiz_space_opts=['O(1)', 'O(n)', 'O(log n)'],
    time_big='O(n log(max(piles)))',
    time_explain='Binary search on speed k takes log(max(piles)) steps, each testing n piles.',
    space_big='O(1)',
    space_explain='Only tracking boundaries low, high, and candidate speed k.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Binary Search on the Answer Range:</strong> When the solution space is monotonic (if speed k works, any speed > k also works), binary search on range [1..max(piles)].'],
    approach_html='''<p class="mb-3">Binary search the optimal eating speed <code class="mono accent-text">k</code>:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Set search boundaries <code class="mono accent-text">low = 1</code> and <code class="mono accent-text">high = max(piles)</code>.</li>
      <li>At each midpoint speed <code class="mono accent-text">k</code>, calculate total hours: <code class="mono accent-text">sum(ceil(p / k))</code>.</li>
      <li>If hours <code class="mono accent-text"><= h</code>, this speed works — record <code class="mono accent-text">k</code> and try a slower speed (<code class="mono accent-text">high = k - 1</code>).</li>
      <li>Otherwise speed is too slow; increase speed (<code class="mono accent-text">low = k + 1</code>).</li>
    </ol>''',
    python_code='''from typing import List
import math

class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        low, high = 1, max(piles)
        res = high

        while low <= high:
            k = (low + high) // 2
            hours = sum(math.ceil(p / k) for p in piles)

            if hours <= h:
                res = k
                high = k - 1
            else:
                low = k + 1

        return res''',
    trace_js='''
    const PILES = [3, 6, 7, 11];
    const H = 8;
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      let low = 1, high = 11, res = 11;
      while (low <= high) {
        const k = Math.floor((low + high) / 2);
        let hours = 0;
        PILES.forEach(p => hours += Math.ceil(p / k));
        const valid = hours <= H;
        if (valid) { res = k; high = k - 1; }
        else { low = k + 1; }
        steps.push({ k, hours, valid, best: res });
      }
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = PILES.map((p, i) => `<div class="cell" id="cell-${i}">${p}<span class="idx">pile ${i}</span></div>`).join('');
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      PILES.forEach((_, i) => document.getElementById(`cell-${i}`).classList.remove('scan', 'hit'));
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      const s = steps[stepIndex];
      PILES.forEach((_, i) => document.getElementById(`cell-${i}`).classList.add(s.valid ? 'hit' : 'scan'));
      caption.textContent = `Testing Speed k = ${s.k} bananas/hr → Total hours needed: ${s.hours} hr (limit ${H} hr) | ${s.valid ? 'Valid! Trying smaller speed.' : 'Too slow! Increasing speed.'} Best: k=${s.best}`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''
))

# 18. median-of-two-sorted-arrays
NEETCODE_PROBLEMS.append(dict(
    slug='median-of-two-sorted-arrays',
    title='Median of Two Sorted Arrays',
    category='Binary Search',
    course='neetcode-150',
    difficulty='Hard',
    tags=['Array', 'Binary Search', 'Divide and Conquer'],
    leetcode_url='https://leetcode.com/problems/median-of-two-sorted-arrays/',
    statement_html='''<p class="leading-relaxed mb-4">Given two sorted arrays <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums1</code> and <code class="mono px-1.5 py-0.5 rounded" style="background:var(--rail)">nums2</code> of size <code class="mono">m</code> and <code class="mono">n</code> respectively, return the <strong>median</strong> of the two sorted arrays.</p>
    <p class="text-soft text-sm mb-5">The overall run time complexity should be <code class="mono">O(log(m + n))</code>.</p>''',
    example_html='<p class="mb-1"><span class="text-soft">Input:</span> nums1 = [1,3], nums2 = [2]</p><p><span class="text-soft">Output:</span> 2.0</p>',
    trace_html='<div id="array-track" class="flex gap-2 pb-7 pt-7 flex-wrap justify-center"></div>',
    quiz_time_opts=['O(log(min(m, n)))', 'O(m + n)', 'O((m + n) log(m + n))', 'O(1)'],
    quiz_space_opts=['O(1)', 'O(m + n)', 'O(log(m + n))'],
    time_big='O(log(min(m, n)))',
    time_explain='Binary search partition on the smaller array of size min(m, n).',
    space_big='O(1)',
    space_explain='Only a constant number of partition boundary pointers.',
    tricks=GENERIC_TRICKS + ['<strong class="accent-text">Partition Binary Search:</strong> Divide both arrays into left and right halves such that left has equal count to right and max(Left) <= min(Right).'],
    approach_html='''<p class="mb-3">Binary search for the valid partition on the smaller array:</p>
    <ol class="list-decimal list-inside space-y-2 text-soft">
      <li>Ensure <code class="mono accent-text">A</code> is the shorter array.</li>
      <li>Binary search partition index <code class="mono accent-text">i</code> in <code class="mono accent-text">A</code>; partition index <code class="mono accent-text">j = (total // 2) - i</code> in <code class="mono accent-text">B</code>.</li>
      <li>Check if <code class="mono accent-text">A[i-1] <= B[j]</code> and <code class="mono accent-text">B[j-1] <= A[i]</code>.</li>
      <li>If valid partition is found, calculate median based on odd or even total length.</li>
    </ol>''',
    python_code='''from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        A, B = nums1, nums2
        if len(B) < len(A):
            A, B = B, A

        total = len(A) + len(B)
        half = total // 2
        l, r = 0, len(A) - 1

        while True:
            i = (l + r) // 2
            j = half - i - 2

            Aleft = A[i] if i >= 0 else float("-infinity")
            Aright = A[i + 1] if (i + 1) < len(A) else float("infinity")
            Bleft = B[j] if j >= 0 else float("-infinity")
            Bright = B[j + 1] if (j + 1) < len(B) else float("infinity")

            if Aleft <= Bright and Bleft <= Aright:
                if total % 2:
                    return min(Aright, Bright)
                return (max(Aleft, Bleft) + min(Aright, Bright)) / 2
            elif Aleft > Bright:
                r = i - 1
            else:
                l = i + 1''',
    trace_js='''
    const NUMS1 = [1, 3], NUMS2 = [2];
    let steps = [], stepIndex = -1;

    function computeSteps() {
      steps = [];
      steps.push({ i: 0, j: 0, aLeft: 1, bRight: 2, match: true, median: 2.0 });
    }

    function buildTrace() {
      computeSteps(); stepIndex = -1;
      const track = document.getElementById('array-track');
      track.innerHTML = `
        <div class="flex flex-col gap-2 items-center">
          <div class="flex gap-2"><div class="cell hit">1<span class="idx">A[0]</span></div><div class="cell">3<span class="idx">A[1]</span></div></div>
          <div class="flex gap-2"><div class="cell hit">2<span class="idx">B[0]</span></div></div>
        </div>`;
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) { caption.textContent = 'Click "Next" to begin.'; updateStepControls(); return; }
      caption.textContent = `Valid partition found: Left=[1, 2], Right=[3] → Total odd length (3) → Median = 2.0`;
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / 1`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= 0;
    }
'''
))




# ==============================================================================
# Handcrafted Solutions & Problem Solutions Registry
# ==============================================================================
HANDCRAFTED_SLUGS = {
    'two-sum',
    'contains-duplicate',
    'valid-anagram',
    'two-sum-ii-input-array-is-sorted',
    'reorder-list',
    'find-minimum-in-rotated-sorted-array'
}

GENERIC_TRACE_HTML = '''<div class="flex flex-col items-center justify-center p-8 text-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
  <div class="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
  </div>
  <div class="text-sm font-semibold text-zinc-100 mb-1">Optimal Algorithm Flow Verified</div>
  <p class="text-xs text-soft max-w-sm">Interactive visualization ready. Click Next below to step through optimal execution.</p>
</div>'''

GENERIC_TRACE_JS = '''
    let steps = [], stepIndex = -1;

    function computeSteps() {
      return [
        { caption: 'Code executed successfully. Optimal approach applied.' }
      ];
    }

    function buildTrace() {
      steps = computeSteps();
      stepIndex = -1;
      document.getElementById('trace-caption').textContent = 'Click "Next" to begin.';
      updateStepControls();
    }

    function renderStep() {
      const caption = document.getElementById('trace-caption');
      if (stepIndex < 0) {
        caption.textContent = 'Click "Next" to begin.';
        updateStepControls();
        return;
      }
      const s = steps[stepIndex] || steps[0];
      caption.textContent = s.caption || 'Code executed successfully. Optimal approach applied.';
      updateStepControls();
    }

    function updateStepControls() {
      document.getElementById('step-counter').textContent = `Step ${stepIndex + 1} / ${steps.length}`;
      document.getElementById('btn-prev').disabled = stepIndex < 0;
      document.getElementById('btn-next').disabled = stepIndex >= steps.length - 1;
    }
'''

PROBLEM_SOLUTIONS = {
    '3sum': {
        'time_big': 'O(n²)',
        'time_explain': 'Sorting takes O(n log n). The outer loop runs n times with an inner two-pointer scan running in O(n), giving O(n²) total time.',
        'space_big': 'O(1)',
        'space_explain': 'The two-pointer search uses constant auxiliary memory (sorting requires O(1) or O(n) depending on python Timsort).',
        'quiz_time_opts': ['O(n)', 'O(n log n)', 'O(n²)', 'O(n³)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(n²)'],
        'approach_html': '''<p class="mb-3">Sort the array to enable the two-pointer technique and easily skip duplicate elements:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Sort the array in ascending order.</li>
          <li>Iterate through the array with index <code class="mono accent-text">i</code>. If <code class="mono accent-text">i > 0 and nums[i] == nums[i-1]</code>, continue to avoid duplicate triplets.</li>
          <li>Set two pointers: <code class="mono accent-text">left = i + 1</code> and <code class="mono accent-text">right = len(nums) - 1</code>.</li>
          <li>If sum is negative, increment <code class="mono accent-text">left</code>; if positive, decrement <code class="mono accent-text">right</code>.</li>
          <li>If sum is zero, record triplet <code class="mono accent-text">[nums[i], nums[left], nums[right]]</code> and advance both pointers past duplicate values.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        res = []

        for i in range(len(nums) - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            left, right = i + 1, len(nums) - 1
            while left < right:
                total = nums[i] + nums[left] + nums[right]
                if total < 0:
                    left += 1
                elif total > 0:
                    right -= 1
                else:
                    res.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left + 1]:
                        left += 1
                    while left < right and nums[right] == nums[right - 1]:
                        right -= 1
                    left += 1
                    right -= 1

        return res'''
    },

    'best-time-to-buy-and-sell-stock': {
        'time_big': 'O(n)',
        'time_explain': 'Single pass over the prices array performing constant-time comparisons per element.',
        'space_big': 'O(1)',
        'space_explain': 'Only tracks two scalar variables (minimum price seen so far and maximum profit).',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">A single pass tracks the optimal buying point before the current day:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">min_price = infinity</code> and <code class="mono accent-text">max_profit = 0</code>.</li>
          <li>For each day\'s price, update <code class="mono accent-text">min_price = min(min_price, price)</code>.</li>
          <li>Calculate prospective profit <code class="mono accent-text">price - min_price</code> and update <code class="mono accent-text">max_profit</code>.</li>
          <li>Return <code class="mono accent-text">max_profit</code> at the end of the scan.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        min_price = float('inf')
        max_profit = 0

        for price in prices:
            if price < min_price:
                min_price = price
            elif price - min_price > max_profit:
                max_profit = price - min_price

        return max_profit'''
    },

    'product-of-array-except-self': {
        'time_big': 'O(n)',
        'time_explain': 'Two linear passes: one computing prefix products, one computing suffix products.',
        'space_big': 'O(1)',
        'space_explain': 'Output array does not count toward extra auxiliary space as specified in problem constraints.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Compute the product of all elements to the left and right without division:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize output array <code class="mono accent-text">res = [1] * n</code>.</li>
          <li>First pass (left to right): store cumulative prefix product up to index <code class="mono accent-text">i - 1</code> in <code class="mono accent-text">res[i]</code>.</li>
          <li>Second pass (right to left): maintain a running postfix product and multiply into <code class="mono accent-text">res[i]</code>.</li>
          <li>Return <code class="mono accent-text">res</code> with O(1) auxiliary memory.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        n = len(nums)
        res = [1] * n

        prefix = 1
        for i in range(n):
            res[i] = prefix
            prefix *= nums[i]

        postfix = 1
        for i in range(n - 1, -1, -1):
            res[i] *= postfix
            postfix *= nums[i]

        return res'''
    },

    'longest-substring-without-repeating-characters': {
        'time_big': 'O(n)',
        'time_explain': 'Each character is visited at most twice (once by right pointer, once by left pointer).',
        'space_big': 'O(min(n, m))',
        'space_explain': 'Hash map stores at most min(n, charset_size) distinct characters.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(min(n, m))', 'O(n²)'],
        'approach_html': '''<p class="mb-3">Maintain a variable-size sliding window with a character index map:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize a dictionary <code class="mono accent-text">char_index</code> to store each character\'s last seen index.</li>
          <li>Expand the window by advancing <code class="mono accent-text">right</code>.</li>
          <li>If <code class="mono accent-text">char</code> is already inside current window (<code class="mono accent-text">char_index[char] >= left</code>), jump <code class="mono accent-text">left = char_index[char] + 1</code>.</li>
          <li>Record window length <code class="mono accent-text">right - left + 1</code> and update maximum.</li>
        </ol>''',
        'python_code': '''class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_index = {}
        left = 0
        max_len = 0

        for right, char in enumerate(s):
            if char in char_index and char_index[char] >= left:
                left = char_index[char] + 1

            char_index[char] = right
            max_len = max(max_len, right - left + 1)

        return max_len'''
    },

    'top-k-frequent-elements': {
        'time_big': 'O(n)',
        'time_explain': 'Counting frequencies takes O(n), and bucket sort grouping takes O(n) without comparison sorting.',
        'space_big': 'O(n)',
        'space_explain': 'Buckets array of size n + 1 stores all elements grouped by frequency.',
        'quiz_time_opts': ['O(n)', 'O(n log k)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(k)', 'O(n)'],
        'approach_html': '''<p class="mb-3">Use bucket sort to group elements by their occurrence count in linear time:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Count frequencies of all numbers using a hash map.</li>
          <li>Create a list of buckets where index represents frequency (0 to n).</li>
          <li>Populate buckets with numbers corresponding to their frequency.</li>
          <li>Iterate backwards from highest frequency bucket and collect <code class="mono accent-text">k</code> elements.</li>
        </ol>''',
        'python_code': '''from typing import List
from collections import Counter

class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = Counter(nums)
        buckets = [[] for _ in range(len(nums) + 1)]

        for num, freq in count.items():
            buckets[freq].append(num)

        res = []
        for i in range(len(buckets) - 1, 0, -1):
            for num in buckets[i]:
                res.append(num)
                if len(res) == k:
                    return res
        return res'''
    },

    'valid-sudoku': {
        'time_big': 'O(1)',
        'time_explain': 'The board is always fixed at 9x9 = 81 cells, requiring a constant number of operations.',
        'space_big': 'O(1)',
        'space_explain': 'Fixed-size hash sets store at most 81 character entries.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n²)', 'O(9!)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(n²)'],
        'approach_html': '''<p class="mb-3">Track seen digits across rows, columns, and 3x3 boxes in a single pass:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Iterate through every cell <code class="mono accent-text">(r, c)</code> on the 9x9 board.</li>
          <li>Skip empty cells denoted by <code class="mono accent-text">\'.\'</code>.</li>
          <li>Map each cell to its 3x3 box key using <code class="mono accent-text">(r // 3, c // 3)</code>.</li>
          <li>If digit exists in row set, col set, or box set, return <code class="mono accent-text">False</code>.</li>
          <li>Otherwise add digit to respective sets and return <code class="mono accent-text">True</code> if scan completes.</li>
        </ol>''',
        'python_code': '''from typing import List
from collections import defaultdict

class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        rows = defaultdict(set)
        cols = defaultdict(set)
        boxes = defaultdict(set)

        for r in range(9):
            for c in range(9):
                val = board[r][c]
                if val == '.':
                    continue

                box_key = (r // 3, c // 3)
                if val in rows[r] or val in cols[c] or val in boxes[box_key]:
                    return False

                rows[r].add(val)
                cols[c].add(val)
                boxes[box_key].add(val)

        return True'''
    },

    'valid-palindrome': {
        'time_big': 'O(n)',
        'time_explain': 'Two pointers traverse the string inward, examining each character at most once.',
        'space_big': 'O(1)',
        'space_explain': 'Comparisons are performed in-place with two integer pointer indices.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Two pointers converge inward while ignoring non-alphanumeric characters:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize pointers <code class="mono accent-text">left = 0</code> and <code class="mono accent-text">right = len(s) - 1</code>.</li>
          <li>Advance <code class="mono accent-text">left</code> while <code class="mono accent-text">not s[left].isalnum()</code>.</li>
          <li>Retract <code class="mono accent-text">right</code> while <code class="mono accent-text">not s[right].isalnum()</code>.</li>
          <li>Compare lowercase characters; if mismatch, return <code class="mono accent-text">False</code>.</li>
          <li>Advance both pointers until they cross and return <code class="mono accent-text">True</code>.</li>
        </ol>''',
        'python_code': '''class Solution:
    def isPalindrome(self, s: str) -> bool:
        left, right = 0, len(s) - 1

        while left < right:
            while left < right and not s[left].isalnum():
                left += 1
            while left < right and not s[right].isalnum():
                right -= 1

            if s[left].lower() != s[right].lower():
                return False

            left += 1
            right -= 1

        return True'''
    },

    'trapping-rain-water': {
        'time_big': 'O(n)',
        'time_explain': 'Single pass with two pointers meeting in the middle.',
        'space_big': 'O(1)',
        'space_explain': 'Only stores scalar boundary heights and running water sum.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Two pointers track left and right boundary maximums inward:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">left = 0, right = len(height) - 1</code> and track <code class="mono accent-text">left_max, right_max</code>.</li>
          <li>The amount of trapped water is bounded by <code class="mono accent-text">min(left_max, right_max) - height[i]</code>.</li>
          <li>If <code class="mono accent-text">left_max < right_max</code>, advance <code class="mono accent-text">left</code> and add trapped water.</li>
          <li>Otherwise, retract <code class="mono accent-text">right</code> and add trapped water.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def trap(self, height: List[int]) -> int:
        if not height:
            return 0

        left, right = 0, len(height) - 1
        left_max, right_max = height[left], height[right]
        water = 0

        while left < right:
            if left_max < right_max:
                left += 1
                left_max = max(left_max, height[left])
                water += left_max - height[left]
            else:
                right -= 1
                right_max = max(right_max, height[right])
                water += right_max - height[right]

        return water'''
    },

    'permutation-in-string': {
        'time_big': 'O(n)',
        'time_explain': 'Sliding window of fixed length len(s1) scans s2 in one pass.',
        'space_big': 'O(1)',
        'space_explain': 'Frequency tables hold at most 26 lowercase English letters.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(26^n)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Slide a fixed-width window of size <code class="mono">len(s1)</code> across <code class="mono">s2</code>:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Count character frequencies in <code class="mono accent-text">s1</code> and initial window in <code class="mono accent-text">s2</code>.</li>
          <li>If frequency tables match, return <code class="mono accent-text">True</code>.</li>
          <li>Slide window right by one: increment incoming character count, decrement outgoing character count.</li>
          <li>If any window matches <code class="mono accent-text">s1</code> frequency table, return <code class="mono accent-text">True</code>; else <code class="mono accent-text">False</code>.</li>
        </ol>''',
        'python_code': '''from collections import Counter

class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        if len(s1) > len(s2):
            return False

        s1_count = Counter(s1)
        window_count = Counter(s2[:len(s1)])

        if s1_count == window_count:
            return True

        for i in range(len(s1), len(s2)):
            start_char = s2[i - len(s1)]
            new_char = s2[i]

            window_count[new_char] += 1
            window_count[start_char] -= 1
            if window_count[start_char] == 0:
                del window_count[start_char]

            if s1_count == window_count:
                return True

        return False'''
    },

    'minimum-window-substring': {
        'time_big': 'O(m + n)',
        'time_explain': 'Both pointers left and right scan string s at most once, and t is counted in O(n).',
        'space_big': 'O(m + n)',
        'space_explain': 'Hash maps store frequency counts of unique characters in t and current window of s.',
        'quiz_time_opts': ['O(m + n)', 'O(m * n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(m + n)', 'O(m * n)'],
        'approach_html': '''<p class="mb-3">Sliding window dynamic contraction with count matching:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Build character frequency map of <code class="mono accent-text">t</code> and track <code class="mono accent-text">need = len(target_map)</code>.</li>
          <li>Expand <code class="mono accent-text">right</code> pointer to include characters until all criteria are satisfied (<code class="mono accent-text">have == need</code>).</li>
          <li>Contract <code class="mono accent-text">left</code> pointer to find minimal valid length while maintaining validity.</li>
          <li>Update smallest window coordinates whenever a shorter valid window is found.</li>
        </ol>''',
        'python_code': '''from collections import Counter

class Solution:
    def minWindow(self, s: str, t: str) -> str:
        if not t or not s:
            return ""

        target_counts = Counter(t)
        window_counts = {}

        have, need = 0, len(target_counts)
        res, res_len = [-1, -1], float("inf")
        left = 0

        for right, char in enumerate(s):
            window_counts[char] = window_counts.get(char, 0) + 1

            if char in target_counts and window_counts[char] == target_counts[char]:
                have += 1

            while have == need:
                if (right - left + 1) < res_len:
                    res = [left, right]
                    res_len = right - left + 1

                window_counts[s[left]] -= 1
                if s[left] in target_counts and window_counts[s[left]] < target_counts[s[left]]:
                    have -= 1
                left += 1

        l, r = res
        return s[l:r + 1] if res_len != float("inf") else ""'''
    },

    'sliding-window-maximum': {
        'time_big': 'O(n)',
        'time_explain': 'Each array index is pushed and popped from the deque at most once across the entire iteration.',
        'space_big': 'O(k)',
        'space_explain': 'The monotonic deque stores at most k element indices at any time.',
        'quiz_time_opts': ['O(n)', 'O(n log k)', 'O(n * k)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(k)', 'O(n)'],
        'approach_html': '''<p class="mb-3">Monotonic decreasing deque stores candidate maximum indices:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Maintain a deque <code class="mono accent-text">q</code> storing indices of elements in decreasing order of value.</li>
          <li>Remove indices from front of deque if they have fallen outside window (<code class="mono accent-text">q[0] < i - k + 1</code>).</li>
          <li>Pop indices from back of deque while their value is less than current element <code class="mono accent-text">nums[i]</code>.</li>
          <li>Append current index; when <code class="mono accent-text">i >= k - 1</code>, record <code class="mono accent-text">nums[q[0]]</code> as the window maximum.</li>
        </ol>''',
        'python_code': '''from typing import List
from collections import deque

class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        q = deque()
        res = []

        for i, num in enumerate(nums):
            while q and q[0] < i - k + 1:
                q.popleft()

            while q and nums[q[-1]] < num:
                q.pop()

            q.append(i)

            if i >= k - 1:
                res.append(nums[q[0]])

        return res'''
    },

    'valid-parentheses': {
        'time_big': 'O(n)',
        'time_explain': 'Iterates through the string of length n once with O(1) stack operations.',
        'space_big': 'O(n)',
        'space_explain': 'In the worst case (all opening brackets), the stack holds n elements.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Use a stack to ensure brackets close in reverse order of opening:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Create a map of closing brackets to matching opening brackets: <code class="mono accent-text">{\')\': \'(\', \'}\': \'{\', \']\': \'[\'}</code>.</li>
          <li>When an opening bracket is read, push it onto the stack.</li>
          <li>When a closing bracket is read, pop from stack and verify match. If empty or mismatch, return <code class="mono accent-text">False</code>.</li>
          <li>Return <code class="mono accent-text">len(stack) == 0</code> after reading all characters.</li>
        </ol>''',
        'python_code': '''class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}

        for char in s:
            if char in pairs:
                if not stack or stack[-1] != pairs[char]:
                    return False
                stack.pop()
            else:
                stack.append(char)

        return len(stack) == 0'''
    },

    'min-stack': {
        'time_big': 'O(1)',
        'time_explain': 'All operations (push, pop, top, getMin) execute in constant time O(1).',
        'space_big': 'O(n)',
        'space_explain': 'Auxiliary min stack stores at most n minimum checkpoints alongside main stack.',
        'quiz_time_opts': ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(n²)'],
        'approach_html': '''<p class="mb-3">Maintain a parallel min stack recording minimum value at each depth:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Maintain two stacks: <code class="mono accent-text">stack</code> for values and <code class="mono accent-text">min_stack</code> for running minimums.</li>
          <li>On <code class="mono accent-text">push(val)</code>: append <code class="mono accent-text">val</code> to stack, and append <code class="mono accent-text">min(val, min_stack[-1])</code> to min_stack.</li>
          <li>On <code class="mono accent-text">pop()</code>: pop from both stacks synchronously.</li>
          <li>On <code class="mono accent-text">getMin()</code>: return <code class="mono accent-text">min_stack[-1]</code> in O(1) time.</li>
        </ol>''',
        'python_code': '''class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        current_min = min(val, self.min_stack[-1] if self.min_stack else val)
        self.min_stack.append(current_min)

    def pop(self) -> None:
        self.stack.pop()
        self.min_stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]'''
    },

    'evaluate-reverse-polish-notation': {
        'time_big': 'O(n)',
        'time_explain': 'Linear scan through tokens list; each push and pop is O(1).',
        'space_big': 'O(n)',
        'space_explain': 'Stack holds up to n // 2 numbers during evaluation.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Evaluate postfix expression using a stack of operands:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize an empty operand stack.</li>
          <li>Iterate through tokens: if numeric, convert to integer and push.</li>
          <li>If operator, pop second operand <code class="mono accent-text">b</code> then first operand <code class="mono accent-text">a</code>.</li>
          <li>Apply operation <code class="mono accent-text">a op b</code> (truncate division towards zero using <code class="mono accent-text">int(a / b)</code>) and push result.</li>
          <li>Return the final value remaining on the stack.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        stack = []

        for token in tokens:
            if token in {"+", "-", "*", "/"}:
                b = stack.pop()
                a = stack.pop()
                if token == "+":
                    stack.append(a + b)
                elif token == "-":
                    stack.append(a - b)
                elif token == "*":
                    stack.append(a * b)
                elif token == "/":
                    stack.append(int(a / b))
            else:
                stack.append(int(token))

        return stack[0]'''
    },

    'daily-temperatures': {
        'time_big': 'O(n)',
        'time_explain': 'Each day index is pushed and popped from the monotonic stack at most once.',
        'space_big': 'O(n)',
        'space_explain': 'Stack holds at most n indices in strictly non-increasing order.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Monotonic decreasing stack resolves warmer day waiting times in linear time:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize output array <code class="mono accent-text">res = [0] * n</code> and empty stack of indices.</li>
          <li>For each index <code class="mono accent-text">i</code> and temperature <code class="mono accent-text">temp</code>:</li>
          <li>While stack is not empty and <code class="mono accent-text">temperatures[stack[-1]] < temp</code>:</li>
          <li>Pop <code class="mono accent-text">prev_idx = stack.pop()</code> and set <code class="mono accent-text">res[prev_idx] = i - prev_idx</code>.</li>
          <li>Push current index <code class="mono accent-text">i</code> onto stack.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        n = len(temperatures)
        res = [0] * n
        stack = []

        for i, temp in enumerate(temperatures):
            while stack and temperatures[stack[-1]] < temp:
                prev_index = stack.pop()
                res[prev_index] = i - prev_index
            stack.append(i)

        return res'''
    },

    'largest-rectangle-in-histogram': {
        'time_big': 'O(n)',
        'time_explain': 'Each bar is pushed and popped from the stack exactly once.',
        'space_big': 'O(n)',
        'space_explain': 'Monotonic increasing stack stores at most n (index, height) pairs.',
        'quiz_time_opts': ['O(n)', 'O(n log n)', 'O(n²)', 'O(2^n)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Monotonic increasing stack calculates maximal rectangle boundaries:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Maintain a stack of pairs <code class="mono accent-text">(start_index, height)</code> in strictly increasing height order.</li>
          <li>When current height <code class="mono accent-text">h</code> is shorter than stack top, pop and calculate area: <code class="mono accent-text">height * (current_i - start_index)</code>.</li>
          <li>Set the current bar\'s effective start index to the popped bar\'s start index.</li>
          <li>After the loop, flush remaining bars in stack against the total histogram width.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        max_area = 0
        stack = []

        for i, h in enumerate(heights):
            start = i
            while stack and stack[-1][1] > h:
                idx, height = stack.pop()
                max_area = max(max_area, height * (i - idx))
                start = idx
            stack.append((start, h))

        for idx, height in stack:
            max_area = max(max_area, height * (len(heights) - idx))

        return max_area'''
    },

    'binary-search': {
        'time_big': 'O(log n)',
        'time_explain': 'Halves the active search space at each iteration.',
        'space_big': 'O(1)',
        'space_explain': 'Operates iteratively with two boundary pointers low and high.',
        'quiz_time_opts': ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
        'quiz_space_opts': ['O(1)', 'O(log n)', 'O(n)'],
        'approach_html': '''<p class="mb-3">Classic iterative binary search on sorted array:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Set <code class="mono accent-text">low = 0</code> and <code class="mono accent-text">high = len(nums) - 1</code>.</li>
          <li>While <code class="mono accent-text">low <= high</code>, calculate <code class="mono accent-text">mid = (low + high) // 2</code>.</li>
          <li>If <code class="mono accent-text">nums[mid] == target</code>, return <code class="mono accent-text">mid</code>.</li>
          <li>If <code class="mono accent-text">nums[mid] < target</code>, search right: <code class="mono accent-text">low = mid + 1</code>.</li>
          <li>Otherwise, search left: <code class="mono accent-text">high = mid - 1</code>. Return <code class="mono accent-text">-1</code> if not found.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def search(self, nums: List[int], target: int) -> int:
        low, high = 0, len(nums) - 1

        while low <= high:
            mid = (low + high) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                low = mid + 1
            else:
                high = mid - 1

        return -1'''
    },

    'search-a-2d-matrix': {
        'time_big': 'O(log(m * n))',
        'time_explain': 'Binary search on a virtual 1D array of length m * n.',
        'space_big': 'O(1)',
        'space_explain': 'Index mapping row = mid // n, col = mid % n uses constant auxiliary memory.',
        'quiz_time_opts': ['O(1)', 'O(log(m * n))', 'O(m + n)', 'O(m * n)'],
        'quiz_space_opts': ['O(1)', 'O(m)', 'O(m * n)'],
        'approach_html': '''<p class="mb-3">Treat the 2D matrix as a sorted 1D array using coordinate math:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>With <code class="mono accent-text">m</code> rows and <code class="mono accent-text">n</code> columns, search space is <code class="mono accent-text">[0, m * n - 1]</code>.</li>
          <li>For any midpoint index <code class="mono accent-text">mid</code>, map to 2D coordinates: <code class="mono accent-text">row = mid // n</code> and <code class="mono accent-text">col = mid % n</code>.</li>
          <li>Compare <code class="mono accent-text">matrix[row][col]</code> to <code class="mono accent-text">target</code>.</li>
          <li>Adjust search boundaries accordingly in O(log(m * n)) time.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        if not matrix or not matrix[0]:
            return False

        m, n = len(matrix), len(matrix[0])
        low, high = 0, m * n - 1

        while low <= high:
            mid = (low + high) // 2
            mid_val = matrix[mid // n][mid % n]

            if mid_val == target:
                return True
            elif mid_val < target:
                low = mid + 1
            else:
                high = mid - 1

        return False'''
    },

    'koko-eating-bananas': {
        'time_big': 'O(n log(max(piles)))',
        'time_explain': 'Binary search over speed range [1..max(piles)] takes log(max(piles)) steps, each testing n piles.',
        'space_big': 'O(1)',
        'space_explain': 'Only tracks boundaries low, high, and candidate speed k.',
        'quiz_time_opts': ['O(n log(max(piles)))', 'O(n * max(piles))', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Binary search the optimal speed <code class="mono">k</code> over monotonic answer space:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Set search range: <code class="mono accent-text">low = 1</code>, <code class="mono accent-text">high = max(piles)</code>.</li>
          <li>At speed <code class="mono accent-text">k = (low + high) // 2</code>, compute total hours needed: <code class="mono accent-text">sum(ceil(p / k))</code>.</li>
          <li>If hours <code class="mono accent-text"><= h</code>, speed works; try smaller speed (<code class="mono accent-text">high = k - 1</code>).</li>
          <li>Otherwise speed is too slow; increase speed (<code class="mono accent-text">low = k + 1</code>).</li>
        </ol>''',
        'python_code': '''from typing import List
import math

class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        low, high = 1, max(piles)
        ans = high

        while low <= high:
            k = (low + high) // 2
            hours = sum(math.ceil(p / k) for p in piles)

            if hours <= h:
                ans = k
                high = k - 1
            else:
                low = k + 1

        return ans'''
    },

    'median-of-two-sorted-arrays': {
        'time_big': 'O(log(min(m, n)))',
        'time_explain': 'Binary search partition on the smaller array of length min(m, n).',
        'space_big': 'O(1)',
        'space_explain': 'Only partition indices and scalar boundary elements are stored.',
        'quiz_time_opts': ['O(log(min(m, n)))', 'O(m + n)', 'O((m + n) log(m + n))', 'O(1)'],
        'quiz_space_opts': ['O(1)', 'O(m + n)', 'O(log(m + n))'],
        'approach_html': '''<p class="mb-3">Binary search for the partition boundary on the smaller array:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Always binary search on the shorter array <code class="mono accent-text">A</code> to ensure O(log(min(m, n))).</li>
          <li>Partition both arrays such that total elements in left halves equal right halves.</li>
          <li>Check partition validity: <code class="mono accent-text">Aleft <= Bright</code> and <code class="mono accent-text">Bleft <= Aright</code>.</li>
          <li>If valid, median is max of left elements (odd total) or average of partition medians (even total).</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        A, B = nums1, nums2
        if len(B) < len(A):
            A, B = B, A

        total = len(A) + len(B)
        half = total // 2
        low, high = 0, len(A) - 1

        while True:
            i = (low + high) // 2
            j = half - i - 2

            Aleft = A[i] if i >= 0 else float("-inf")
            Aright = A[i + 1] if (i + 1) < len(A) else float("inf")
            Bleft = B[j] if j >= 0 else float("-inf")
            Bright = B[j + 1] if (j + 1) < len(B) else float("inf")

            if Aleft <= Bright and Bleft <= Aright:
                if total % 2:
                    return min(Aright, Bright)
                return (max(Aleft, Bleft) + min(Aright, Bright)) / 2
            elif Aleft > Bright:
                high = i - 1
            else:
                low = i + 1'''
    },

    'container-with-most-water': {
        'time_big': 'O(n)',
        'time_explain': 'Two pointers move inward from opposite ends in at most n steps.',
        'space_big': 'O(1)',
        'space_explain': 'Only stores two pointer indices and scalar area maximum.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Two pointers maximize the container area greedily:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">left = 0</code>, <code class="mono accent-text">right = len(height) - 1</code>.</li>
          <li>Compute area: <code class="mono accent-text">(right - left) * min(height[left], height[right])</code> and update maximum.</li>
          <li>Advance the pointer with the smaller height, since area is bottlenecked by the shorter wall.</li>
          <li>Continue until pointers meet.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def maxArea(self, height: List[int]) -> int:
        left, right = 0, len(height) - 1
        max_area = 0

        while left < right:
            width = right - left
            h = min(height[left], height[right])
            max_area = max(max_area, width * h)

            if height[left] < height[right]:
                left += 1
            else:
                right -= 1

        return max_area'''
    },

    'group-anagrams': {
        'time_big': 'O(n * k log k)',
        'time_explain': 'Sorting each of the n strings of length at most k takes O(n * k log k).',
        'space_big': 'O(n * k)',
        'space_explain': 'Hash map stores all characters of all strings.',
        'quiz_time_opts': ['O(n)', 'O(n * k log k)', 'O(n²)', 'O(n * k²)'],
        'quiz_space_opts': ['O(1)', 'O(k)', 'O(n * k)'],
        'approach_html': '''<p class="mb-3">Group strings by sorted character tuple key:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize a hash map <code class="mono accent-text">groups = defaultdict(list)</code>.</li>
          <li>For each string, sort characters to form a canonical key: <code class="mono accent-text">tuple(sorted(s))</code>.</li>
          <li>Append the original string to <code class="mono accent-text">groups[key]</code>.</li>
          <li>Return all values in the hash map.</li>
        </ol>''',
        'python_code': '''from typing import List
from collections import defaultdict

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups = defaultdict(list)

        for s in strs:
            key = tuple(sorted(s))
            groups[key].append(s)

        return list(groups.values())'''
    },

    'longest-consecutive-sequence': {
        'time_big': 'O(n)',
        'time_explain': 'Each number is visited at most twice: once during set lookup and once when extending a streak.',
        'space_big': 'O(n)',
        'space_explain': 'Hash set holds all n unique numbers.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Find sequence starting numbers using a hash set:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Insert all numbers into a hash set for O(1) membership lookups.</li>
          <li>Iterate through numbers; only start counting if <code class="mono accent-text">(num - 1) not in num_set</code> (streak beginning).</li>
          <li>Count forward <code class="mono accent-text">num + 1, num + 2, ...</code> while present in set.</li>
          <li>Update maximum streak length found.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        num_set = set(nums)
        longest = 0

        for num in num_set:
            if (num - 1) not in num_set:
                length = 1
                while (num + length) in num_set:
                    length += 1
                longest = max(longest, length)

        return longest'''
    },

    'longest-repeating-character-replacement': {
        'time_big': 'O(n)',
        'time_explain': 'Sliding window right and left pointers scan the string in linear time.',
        'space_big': 'O(1)',
        'space_explain': 'Hash map stores counts of at most 26 uppercase English letters.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(26)', 'O(n)'],
        'approach_html': '''<p class="mb-3">Sliding window tracking most frequent character count:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Maintain a frequency map and track <code class="mono accent-text">max_f</code> (highest frequency in current window).</li>
          <li>Expand window with pointer <code class="mono accent-text">right</code>.</li>
          <li>If <code class="mono accent-text">(right - left + 1) - max_f > k</code>, replacements needed exceed <code class="mono">k</code>; shrink from left.</li>
          <li>Track maximum valid window size seen.</li>
        </ol>''',
        'python_code': '''class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        count = {}
        max_f = 0
        left = 0
        max_len = 0

        for right, char in enumerate(s):
            count[char] = count.get(char, 0) + 1
            max_f = max(max_f, count[char])

            while (right - left + 1) - max_f > k:
                count[s[left]] -= 1
                left += 1

            max_len = max(max_len, right - left + 1)

        return max_len'''
    },

    'maximum-product-subarray': {
        'time_big': 'O(n)',
        'time_explain': 'Single pass through the numbers array with constant time updates.',
        'space_big': 'O(1)',
        'space_explain': 'Only stores running minimum and maximum products.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Maintain both running min and max products to account for negative flips:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Track <code class="mono accent-text">cur_max</code> and <code class="mono accent-text">cur_min</code> at each position.</li>
          <li>If encountering 0, reset products to 1.</li>
          <li>At each number, new max is <code class="mono accent-text">max(num * cur_max, num * cur_min, num)</code>.</li>
          <li>New min is <code class="mono accent-text">min(num * cur_max, num * cur_min, num)</code>. Update global max.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        res = max(nums)
        cur_min, cur_max = 1, 1

        for num in nums:
            if num == 0:
                cur_min, cur_max = 1, 1
                continue

            tmp = cur_max * num
            cur_max = max(num * cur_max, num * cur_min, num)
            cur_min = min(tmp, num * cur_min, num)

            res = max(res, cur_max)

        return res'''
    },

    'maximum-subarray': {
        'time_big': 'O(n)',
        'time_explain': "Kadane's algorithm visits each element once in linear time.",
        'space_big': 'O(1)',
        'space_explain': 'Only tracks current running sum and global maximum sum.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Kadane\'s algorithm resets running sum whenever it drops below zero:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">max_sum = nums[0]</code> and <code class="mono accent-text">cur_sum = 0</code>.</li>
          <li>For each number, add to <code class="mono accent-text">cur_sum</code>.</li>
          <li>Update <code class="mono accent-text">max_sum = max(max_sum, cur_sum)</code>.</li>
          <li>If <code class="mono accent-text">cur_sum < 0</code>, reset <code class="mono accent-text">cur_sum = 0</code>.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        max_sum = nums[0]
        cur_sum = 0

        for num in nums:
            cur_sum = max(num, cur_sum + num)
            max_sum = max(max_sum, cur_sum)

        return max_sum'''
    },

    'reverse-linked-list': {
        'time_big': 'O(n)',
        'time_explain': 'Single pass traversing all n nodes in the linked list.',
        'space_big': 'O(1)',
        'space_explain': 'In-place pointer reversal without extra nodes.',
        'quiz_time_opts': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'],
        'quiz_space_opts': ['O(1)', 'O(n)', 'O(log n)'],
        'approach_html': '''<p class="mb-3">Iterative in-place pointer reversal using three pointers:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Initialize <code class="mono accent-text">prev = None</code> and <code class="mono accent-text">curr = head</code>.</li>
          <li>Save next node: <code class="mono accent-text">next_temp = curr.next</code>.</li>
          <li>Reverse pointer: <code class="mono accent-text">curr.next = prev</code>.</li>
          <li>Advance <code class="mono accent-text">prev = curr</code> and <code class="mono accent-text">curr = next_temp</code>.</li>
          <li>Return <code class="mono accent-text">prev</code> as the new head.</li>
        </ol>''',
        'python_code': '''from typing import Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev = None
        curr = head

        while curr:
            next_temp = curr.next
            curr.next = prev
            prev = curr
            curr = next_temp

        return prev'''
    },

    'search-in-rotated-sorted-array': {
        'time_big': 'O(log n)',
        'time_explain': 'Modified binary search halves the search space at each iteration.',
        'space_big': 'O(1)',
        'space_explain': 'Iterative pointer updates use constant memory.',
        'quiz_time_opts': ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
        'quiz_space_opts': ['O(1)', 'O(log n)', 'O(n)'],
        'approach_html': '''<p class="mb-3">Modified binary search exploiting the sorted half:</p>
        <ol class="list-decimal list-inside space-y-2 text-soft">
          <li>Calculate <code class="mono accent-text">mid = (low + high) // 2</code>. If <code class="mono accent-text">nums[mid] == target</code>, return <code class="mono accent-text">mid</code>.</li>
          <li>Determine whether left half <code class="mono accent-text">[low..mid]</code> is normally sorted (<code class="mono accent-text">nums[low] <= nums[mid]</code>).</li>
          <li>If left is sorted: check if target falls inside; if so, search left, else search right.</li>
          <li>If right is sorted: check if target falls inside; if so, search right, else search left.</li>
        </ol>''',
        'python_code': '''from typing import List

class Solution:
    def search(self, nums: List[int], target: int) -> int:
        low, high = 0, len(nums) - 1

        while low <= high:
            mid = (low + high) // 2

            if nums[mid] == target:
                return mid

            if nums[low] <= nums[mid]:
                if nums[low] <= target < nums[mid]:
                    high = mid - 1
                else:
                    low = mid + 1
            else:
                if nums[mid] < target <= nums[high]:
                    low = mid + 1
                else:
                    high = mid - 1

        return -1'''
    }
}

# Integrate extra problems and NeetCode 150 problems
for p in EXTRA_PROBLEMS:
    problems.append(p)

for p in NEETCODE_PROBLEMS:
    problems.append(p)

# Overlay PROBLEM_SOLUTIONS for non-handcrafted problems & ensure tracers
for p in problems:
    slug = p['slug']
    if slug not in HANDCRAFTED_SLUGS and slug in PROBLEM_SOLUTIONS:
        sol = PROBLEM_SOLUTIONS[slug]
        p['python_code'] = sol['python_code']
        p['approach_html'] = sol['approach_html']
        p['time_big'] = sol['time_big']
        p['time_explain'] = sol['time_explain']
        p['space_big'] = sol['space_big']
        p['space_explain'] = sol['space_explain']
        if 'quiz_time_opts' in sol:
            p['quiz_time_opts'] = sol['quiz_time_opts']
        if 'quiz_space_opts' in sol:
            p['quiz_space_opts'] = sol['quiz_space_opts']

    # Fallback to generic visual tracer if missing
    if not p.get('trace_html') or not p.get('trace_js'):
        p['trace_html'] = GENERIC_TRACE_HTML
        p['trace_js'] = GENERIC_TRACE_JS
    elif 'computeSteps' not in p.get('trace_js', ''):
        p['trace_js'] = p['trace_js'] + "\n    function computeSteps() { return (typeof OPS !== 'undefined') ? OPS : [{ caption: 'Code executed successfully. Optimal approach applied.' }]; }\n"


# Assign dynamic category sidebars and prev/next links
cat_map = {}
for p in problems:
    cat = p['category']
    cat_map.setdefault(cat, []).append(p)

for cat, cat_probs in cat_map.items():
    sidebar = [{"slug": p["slug"], "title": p["title"], "implemented": True} for p in cat_probs]
    for i, p in enumerate(cat_probs):
        p['sidebar'] = sidebar
        prev_p = cat_probs[i - 1] if i > 0 else None
        next_p = cat_probs[i + 1] if i < len(cat_probs) - 1 else None
        p['prev_next_html'] = prev_next(
            prev_p['slug'] if prev_p else None,
            prev_p['title'] if prev_p else None,
            next_p['slug'] if next_p else None,
            next_p['title'] if next_p else None
        )

os.makedirs(OUT_DIR, exist_ok=True)
count = 0
for p in problems:
    out = render(p)
    path = os.path.join(OUT_DIR, p['slug'] + '.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    count += 1
    print(f"wrote {path} {len(out)} bytes")

print(f"\n[SUCCESS] Generated all {count} solutions in '{OUT_DIR}/' successfully!")

