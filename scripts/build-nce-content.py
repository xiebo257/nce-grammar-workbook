#!/usr/bin/env python3
"""Render the reviewed transcription for NCE Lessons 1–48.

Edit nce1/textbook-lessons.json, then run python3 scripts/build-nce-content.py.
Existing grammar exercises, notes, and navigation are preserved.
"""
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / 'nce1'
BEGIN = '      <!-- BEGIN GENERATED TEXTBOOK -->'
END = '      <!-- END GENERATED TEXTBOOK -->'


def escape(value):
  return html.escape(str(value), quote=True).replace('\n', '<br>')


def illustration(item, caption='', eager=False):
  loading = '' if eager else ' loading="lazy"'
  width, height = item['size']
  return f'''<figure class="lesson-illustration">
          <img src="{escape(item['path'])}" width="{width}" height="{height}" alt="{escape(item['alt'])}"{loading} decoding="async">
          {f'<figcaption>{escape(caption)}</figcaption>' if caption else ''}
        </figure>'''


def table(data):
  head = ''.join(f'<th scope="col">{escape(h)}</th>' for h in data['headers'])
  rows = ''.join('<tr>' + ''.join(f'<td>{escape(c)}</td>' for c in row) + '</tr>' for row in data['rows'])
  return f'<div class="table-scroll"><table class="textbook-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def exercise(group, prefix):
  title = group['title']
  parts = [f'        <h4>{escape(title)}</h4>', f'        <p>{escape(group["instruction"])}</p>']
  if group.get('passage'):
    parts.append(f'        <div class="dialogue">{escape(group["passage"])}</div>')
  if group.get('table'):
    parts.append(table(group['table']))
  if group.get('example'):
    parts.append(f'        <p class="worked-example"><strong>Example · 例句</strong><br>{escape(group["example"])}</p>')
  start = group.get('start', 1)
  parts.append(f'        <ol start="{start}">')
  for i, prompt in enumerate(group['items']):
    index = i + start
    key = f'{prefix}-{index}'
    label = f'{title}, item {index}'
    previous = group.get('previousIndices', [None] * len(group['items']))[i]
    migration = f' data-previous-index="{previous}"' if previous is not None else ''
    parts.append(f'''          <li>
            <div class="question-text" id="prompt-{key}"><span class="exercise-label">{escape(prefix.split('-')[0])}: {escape(title)} — </span>{escape(prompt)}</div>
            <textarea class="answer-field" rows="{group.get('rows', 2)}" aria-label="{escape(label)}" aria-describedby="prompt-{key}"{migration}></textarea>
          </li>''')
  parts.append('        </ol>')
  return '\n'.join(line.rstrip() for line in '\n'.join(parts).splitlines())


def render(number, lesson):
  parts = [BEGIN, '''      <section class="lesson-section" id="lesson-content" aria-labelledby="content-heading">
        <h2 id="content-heading">Lesson content · 课文</h2>''',
    f'        <h3>{escape(lesson["title"])} · {escape(lesson["chineseTitle"])}</h3>']
  if lesson.get('comprehension'):
    parts.append(f'        <p>{escape(lesson["listeningInstruction"])}<br><strong>{escape(lesson["comprehension"])}</strong><br>{escape(lesson["comprehensionChinese"])}</p>')
  if lesson.get('text'):
    parts.append('        <div class="reading-layout"><div class="dialogue">')
    parts.extend(f'          <p>{escape(line)}</p>' for line in lesson['text'])
    parts.append('        </div><div class="reading-art">')
    parts.extend(illustration(item, eager=i == 0) for i, item in enumerate(lesson['illustrations']))
    parts.append('        </div></div>')
  if lesson['oral']:
    parts.append(f'        <p>{escape(lesson["oralInstruction"])}</p>')
    parts.extend(f'        <p class="worked-example">{escape(pattern)}</p>' for pattern in lesson.get('oralPatterns', []))
    parts.append('        <div class="oral-grid">')
    for i, (item, image) in enumerate(zip(lesson['oral'], lesson['illustrations'])):
      parts.append(illustration(image, item['label'] + (' · ' + item['caption'] if item['caption'] else ''), eager=i < 2))
    parts.append('        </div>')
  if lesson['vocabulary']:
    parts.append('        <h3>New words and expressions · 生词和短语</h3>')
    parts.append(table({'headers': ['Word · 单词', 'Pronunciation · 音标', 'Meaning · 词义'], 'rows': [[v['word'], '/' + v['ipa'] + '/', v['meaning']] for v in lesson['vocabulary']]}))
  if lesson['notes']:
    parts.append('        <h3>Notes on the text · 课文注释</h3><ol class="text-notes">')
    parts.extend(f'          <li>{escape(note)}</li>' for note in lesson['notes'])
    parts.append('        </ol>')
  if lesson['translation']:
    parts.append('        <h3>Chinese translation · 参考译文</h3><div class="translation" lang="zh-Hans">')
    parts.extend(f'          <p>{escape(line)}</p>' for line in lesson['translation'])
    parts.append('        </div>')
  parts.append(f'''      </section>
      <section class="lesson-section" id="textbook-practice" aria-labelledby="practice-heading" data-previous-count="{lesson['previousPracticeCount']}">
        <h2 id="practice-heading">Practice · 课文练习</h2>''')
  if lesson.get('comprehension'):
    parts.append('        <h3>Understand the lesson · 课文理解</h3>')
    parts.append(exercise({'title': 'Comprehension · 理解题', 'instruction': 'Answer the question about the lesson text. 根据课文回答问题。', 'items': [lesson['comprehension']], 'previousIndices': [0]}, 'comprehension'))
  if lesson['written']:
    parts.append('        <h3>Written exercises · 书面练习</h3>')
    parts.extend(exercise(group, f'textbook-{i}') for i, group in enumerate(lesson['written']))
  parts.append('        <h3>Practice worksheet · 配套练习</h3>')
  parts.extend(exercise(group, f'worksheet-{i}') for i, group in enumerate(lesson['practice']))
  if lesson.get('previousCustomPractice'):
    parts.append('        <details class="extra-review"><summary>Extra review · 补充复习</summary>')
    parts.append(exercise(lesson['previousCustomPractice'], 'review'))
    parts.append('        </details>')
  parts += ['      </section>', END]
  return '\n'.join(line.rstrip() for line in '\n'.join(parts).splitlines())


def main():
  data = json.loads((LESSONS / 'textbook-lessons.json').read_text())
  assert set(data) == {str(n) for n in range(1, 49)}
  for number in range(1, 49):
    page = LESSONS / f'lesson-{number:03}.html'
    source = page.read_text()
    lesson = data[str(number)]
    for image in lesson['illustrations']:
      assert (LESSONS / image['path']).is_file(), image['path']
    generated = render(number, lesson)
    if BEGIN in source:
      start = source.index(BEGIN)
      end = source.index(END, start) + len(END)
      source = source[:start] + generated + source[end:]
    elif 'id="grammar-practice"' in source:
      # The initial Lesson 1 revision already wrapped its original grammar.
      start = source.index('    <article>') + len('    <article>')
      end = source.index('      <section class="lesson-section" id="grammar-practice"', start)
      source = source[:start] + '\n' + generated + '\n' + source[end:]
    else:
      start = source.index('    <article>') + len('    <article>')
      end = source.index('      <section class="lesson-notes"', start)
      grammar = source[start:end].strip()
      grammar = re.sub(r'<p[^>]*>Source:.*?</p>\s*', '', grammar, flags=re.S)
      grammar = grammar.replace('<h2', '<h3').replace('</h2>', '</h3>')
      grammar = '\n'.join('        ' + line.lstrip() for line in grammar.splitlines())
      source = source[:start] + '\n' + generated + '''
      <section class="lesson-section" id="grammar-practice" aria-labelledby="grammar-heading">
        <h2 id="grammar-heading">Grammar practice · 语法练习</h2>
''' + grammar + '\n      </section>\n' + source[end:]
    if 'href="lesson-content.css"' not in source:
      source = source.replace('  <link rel="stylesheet" href="lesson-navigation.css">', '  <link rel="stylesheet" href="lesson-navigation.css">\n  <link rel="stylesheet" href="lesson-content.css">')
    if 'src="lesson-content.js"' not in source:
      source = source.replace('  <script>\n', '  <script src="lesson-content.js"></script>\n  <script>\n', 1)
    page.write_text(source)
  print('Rebuilt complete textbook content and practice for Lessons 1–48.')


if __name__ == '__main__':
  main()
