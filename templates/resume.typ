// Data-driven resume built on @preview/tech-focused-resume (MIT).
// All profile text arrives via data.json as strings, never as Typst code.
#import "@preview/tech-focused-resume:0.1.2": *

#let data = json("data.json")
#let p = data.profile
#let labels = data.labels

#show: resume.with(
  header-info: (
    style: "row",
    contact: (show-icons: true, show-sensitive-info: true, position: left, gap: 0.4em, info: default-contact-info),
    author: (name: "", headline: "", position: left, uppercase: false),
  ),
  style: (
    accent-color: "#000000", font: "Libertinus Serif", paper: "a4", font-size: 10pt,
    margin: (top: 0.45in, bottom: 0.4in, left: 0.5in, right: 0.5in),
  ),
  config: (lang: data.language, region: data.region),
  document-metadata: (title: p.name, description: "Resume", keywords: "cv"),
)

// Two-column header: identity and contacts on the left, photo on the right.
// The package header above is intentionally empty; this grid replaces it.
#grid(
  columns: (1fr, auto),
  align: (left, top + right),
  column-gutter: 14pt,
  block[
    #author-title(author: (name: p.name, headline: "", position: left, uppercase: false), font-size: 10pt)
    #v(0.3em)
    #contact-info(config: (info: data.contacts, show-icons: true, show-sensitive-info: true, position: left, gap: 0.4em))
  ],
  if data.photo != none { image(data.photo, height: 96pt) },
)
#v(-0.5em)

// Render every supplied string as text, preserving explicit line breaks.
#let plain(value) = {
  let lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
  for (index, item) in lines.enumerate() {
    if index > 0 { linebreak() }
    text(item)
  }
}
#let entry-dates(entry) = dates-helper(start-date: entry.start, end-date: if entry.end == none { labels.current } else { entry.end })

#if p.experience.len() > 0 {
  section(labels.experience)[
    #for entry in p.experience {
      work(
        company: entry.company,
        title: entry.title,
        dates: entry-dates(entry),
        location: if p.at("location", default: none) == none { "" } else { p.at("location", default: none) },
      )[
        #(if entry.bullets.len() > 0 { list(..entry.bullets.map(bullet => plain(bullet))) } else { [] })
      ]
    }
  ]
}

#if p.education.len() > 0 {
  section(labels.education)[
    #for entry in p.education {
      edu(
        institution: entry.institution,
        degree: entry.degree,
        dates: if entry.start == none and entry.end == none { "" } else { dates-helper(start-date: if entry.start == none { "" } else { entry.start }, end-date: if entry.end == none { "" } else { entry.end }) },
        location: if p.at("location", default: none) == none { "" } else { p.at("location", default: none) },
      )[]
    }
  ]
}

#if p.skills.len() > 0 {
  section(labels.skills)[
    #skills[
      #(plain(p.skills.join(" · ")))
    ]
  ]
}

#if p.languages.len() > 0 {
  section(labels.languages)[
    #languages[
      #(plain(p.languages.join(" · ")))
    ]
  ]
}

#if p.certifications.len() > 0 {
  section(labels.certifications)[
    #for entry in p.certifications {
      certificates(name: plain(entry))
    }
  ]
}
