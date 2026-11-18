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
    margin: (top: 0.35in, bottom: 0.35in, left: 0.4in, right: 0.4in),
  ),
  config: (lang: data.language, region: data.region),
  document-metadata: (title: p.name, description: "Resume", keywords: "cv"),
)
// Tighter rhythm keeps the two-page limit with full experience history.
#set list(spacing: 0.4em)
#show heading: set block(above: 7pt, below: 14pt)

// Two-column header: identity and contacts on the left, photo on the right.
// The package header above is intentionally empty; this grid replaces it.
#grid(
  columns: (1fr, auto),
  align: (left, bottom + right),
  column-gutter: 14pt,
  block[
    #author-title(author: (name: p.name, headline: "", position: left, uppercase: false), font-size: 10pt)
    #text(fill: luma(60%), size: 10pt * 1.5)[#if p.at("headline", default: none) == none { [] } else { p.headline }]
    #v(0.4em)
    // All contacts on one line: phone · linkedin · email · location.
    #contact-item(data.contacts.phone, icon-name: "phone", show-icons: true)
    #h(0.4em)
    #sym.dot.c
    #h(0.4em)
    #contact-item(data.contacts.linkedin, prefix: "linkedin.com/in/", link-type: "https://", icon-name: "linkedin", show-icons: true)
    #h(0.4em)
    #sym.dot.c
    #h(0.4em)
    #contact-item(data.contacts.email, prefix: "", link-type: "mailto:", icon-name: "envelope", show-icons: true)
    #h(0.4em)
    #sym.dot.c
    #h(0.4em)
    #contact-item(data.contacts.location)
  ],
)

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
        // The package renders "modality — location"; when there is no modality,
        // carry the location in its slot to avoid a leading dash.
        modality: if entry.at("modality", default: none) == none {
          if entry.at("location", default: none) == none { "" } else { entry.location }
        } else { labels.modalities.at(entry.modality) },
        location: if entry.at("modality", default: none) == none { "" } else { if entry.at("location", default: none) == none { "" } else { entry.location } },
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

#let skill-list = if p.skills.len() > 0 { skills[
  #for group in p.skills {
    if type(group) == str {
      [- #plain(group)]
    } else {
      [- *#group.label:* #plain(group.items.join(", "))]
    }
  }
] }
#let language-list = if p.languages.len() > 0 { languages[
  #for lang in p.languages {
    [- #plain(lang)]
  }
] }

#if p.skills.len() > 0 and p.languages.len() > 0 {
  grid-section(columns: (1fr, 1fr), gutter: 2em, sections: (
    section(labels.skills)[#skill-list],
    section(labels.languages)[#language-list],
  ))
} else {
  if p.skills.len() > 0 { section(labels.skills)[#skill-list] }
  if p.languages.len() > 0 { section(labels.languages)[#language-list] }
}

#if p.certifications.len() > 0 {
  section(labels.certifications)[
    #for (index, entry) in p.certifications.enumerate() {
      if index > 0 { linebreak() }
      let date = if type(entry) == str { "" } else { if entry.at("expires", default: none) == none { if entry.at("issued", default: none) == none { "" } else { entry.issued } } else { dates-helper(start-date: entry.issued, end-date: entry.expires) } }
      let parts = if type(entry) == str { (entry,) } else { (entry.name, ..if entry.at("issuer", default: none) == none { () } else { (entry.issuer,) }, date) }
      plain(parts.filter(part => part != "").join(" · "))
    }
  ]
}
