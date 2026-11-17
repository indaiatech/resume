#let data = json("data.json")
#let p = data.profile
#let labels = data.labels
#set document(title: p.name, author: p.name)
#set page(paper: "a4", margin: (x: 17mm, y: 15mm))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: data.language)
#set par(justify: false, leading: 0.55em, spacing: 5pt)
#set list(indent: 10pt, body-indent: 5pt, spacing: 2pt)

// Render every supplied string as text, preserving explicit line breaks.
#let plain(value) = {
  let lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
  for (index, item) in lines.enumerate() {
    if index > 0 { linebreak() }
    text(item)
  }
}
#let dates(start, end) = plain((start, end).filter(x => x != none and x != "").join(" – "))
#let section(title) = block(above: 9pt, below: 4pt, width: 100%, sticky: true)[
  #text(11pt, weight: "bold", title)
  #v(-5pt)
  #line(length: 100%, stroke: 0.5pt)
]

#align(center)[
  #text(19pt, weight: "bold", plain(p.name))
  #v(3pt)
  #for (index, contact) in data.contacts.enumerate() {
    if index > 0 { [ #h(3pt)·#h(3pt) ] }
    if contact.target != none {
      link(contact.target, plain(contact.text))
    } else {
      plain(contact.text)
    }
  }
]

#if p.experience.len() > 0 {
  section(labels.experience)
  for entry in p.experience {
    block(above: 5pt, below: 2pt, breakable: false)[
      #text(weight: "bold", plain(entry.title)) — #plain(entry.company)
      #linebreak()
      #text(style: "italic")[
        #dates(entry.start, if entry.end == none { labels.current } else { entry.end })
        #if entry.location != none and entry.location != "" { [ · #plain(entry.location)] }
      ]
    ]
    if entry.bullets.len() > 0 {
      list(..entry.bullets.map(bullet => plain(bullet)))
    }
  }
}

#if p.education.len() > 0 {
  section(labels.education)
  for entry in p.education {
    block(above: 4pt, below: 2pt, breakable: false)[
      #text(weight: "bold", plain(entry.institution))
      #linebreak()
      #plain(entry.degree)
      #if entry.start != none or entry.end != none {
        [ · #dates(entry.start, entry.end)]
      }
    ]
  }
}

#for (field, title) in (
  ("skills", labels.skills),
  ("languages", labels.languages),
  ("certifications", labels.certifications),
) {
  let entries = p.at(field)
  if entries.len() > 0 {
    section(title)
    plain(entries.join("; "))
  }
}
