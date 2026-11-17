#let data = json("data.json")
#let p = data.profile
#set document(title: p.name, author: p.name)
#set page(paper: "a4", margin: (x: 22mm, y: 20mm))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: data.language)
#set par(justify: false, leading: 0.65em, spacing: 12pt)

#let plain(value) = {
  let lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
  for (index, item) in lines.enumerate() {
    if index > 0 { linebreak() }
    text(item)
  }
}

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
#v(14pt)
#par(plain(data.labels.greeting))
#for paragraph in data.paragraphs {
  par(plain(paragraph))
}
#block(breakable: false)[
  #plain(data.labels.closing)
  #linebreak()
  #plain(p.name)
]
