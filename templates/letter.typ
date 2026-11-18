// Data-driven cover letter built on @preview/exp-cover-letter (public domain).
// All letter text arrives via data.json as strings, never as Typst code.
#import "@preview/exp-cover-letter:0.1.0": *

#let data = json("data.json")
#let p = data.profile

// Render every supplied string as text, preserving explicit line breaks.
#let plain(value) = {
  let lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
  for (index, item) in lines.enumerate() {
    if index > 0 { linebreak() }
    text(item)
  }
}

#show: letter.with(
  font: "Libertinus Serif",
  paper: "a4",
  font-size: 11pt,
  lang: data.language,
  date: data.date,
  closing: data.labels.closing,
)

#sender(
  author: p.name,
  location: if p.location == none { "" } else { p.location },
  email: if p.email == none { "" } else { p.email },
  phone: if p.phone == none { "" } else { p.phone },
  linkedin: data.contacts.linkedin,
  github: data.contacts.github,
  personal-site: data.contacts.personal-site,
)

#recipient(greeting: data.labels.greeting)

#for paragraph in data.paragraphs {
  plain(paragraph)
}
