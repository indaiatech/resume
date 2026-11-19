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
// Consistent list rhythm; profile metadata controls which roles show details.
#set list(spacing: 0.4em)
// Section title rendered directly (no heading element) so the package's
// heading wrapper cannot double the underline or pull it into the text.
#let mysection(title, body) = {
  // Bottom border hugs the text; a line() element would drift with paragraph spacing.
  block(above: 16pt, below: 6pt, width: 100%, stroke: (bottom: 0.5pt), inset: (bottom: 3pt))[
    #set text(size: 11pt, weight: "bold")
    #smallcaps(title)
  ]
  pad(left: 1.4em, body)
}

// Contacts spread across the line: every supplied block shares the width,
// first left, last right, middles centered. With all four blocks the original
// proportions (wider email column) are preserved.
#let contact-definitions = (
  (value: data.contacts.phone, align: left, cell: contact-item(data.contacts.phone, icon-name: "phone", show-icons: true)),
  (value: data.contacts.linkedin, align: center, cell: contact-item(data.contacts.linkedin, prefix: "linkedin.com/in/", link-type: "https://", icon-name: "linkedin", show-icons: true)),
  (value: data.contacts.email, align: center, cell: contact-item(data.contacts.email, prefix: "", link-type: "mailto:", icon-name: "envelope", show-icons: true)),
  (value: data.contacts.location, align: right, cell: contact-item(data.contacts.location)),
)
#let present-contacts = contact-definitions.filter(entry => entry.value != "")
#let contact-columns = if present-contacts.len() == 4 { (1fr, 1fr, 1.5fr, 1fr) } else { (1fr,) * present-contacts.len() }
#let contact-aligns = if present-contacts.len() == 1 { (center,) } else {
  range(present-contacts.len()).map(index => if index == 0 { left } else if index == present-contacts.len() - 1 { right } else { center })
}
// Explicit stack gaps avoid paragraph margins above and below the role line.
#stack(
  spacing: 1em,
  author-title(
    author: (name: p.name, headline: "", position: center, uppercase: false),
    font-size: 10pt,
  ),
  ..(if p.at("headline", default: none) != none and p.headline != "" {
    // Long role lists shrink slightly to stay on one centered line.
    let roles-size = if p.headline.len() > 60 { 10pt * 1.2 } else { 10pt * 1.5 }
    (align(center, text(fill: luma(60%), size: roles-size, p.headline)),)
  } else { () }),
  grid(
    columns: contact-columns,
    align: contact-aligns.map(horizontal => horizontal + bottom),
    ..present-contacts.map(entry => entry.cell),
  ),
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

#if p.at("summary", default: none) != none and p.summary != "" {
  mysection(labels.summary)[#plain(p.summary)]
}

#let detailed-experience = p.experience.filter(entry => not entry.at("collapse", default: false))
#let earlier-experience = p.experience.filter(entry => entry.at("collapse", default: false))

// Stealth engagements hide the client name behind the localized NDA label.
#let display-company(entry) = if entry.at("stealth", default: false) { labels.stealth_client } else { entry.company }
#let contractor-mark(entry) = if entry.at("contractor", default: false) [ #sym.dot.c #emph(labels.contract)] else []

#if detailed-experience.len() > 0 {
  mysection(labels.experience)[
    #for entry in detailed-experience {
      // Same two-by-two structure as the package's work(), so the
      // modality—location line can be styled locally.
      let modality = if entry.at("modality", default: none) == none {
        if entry.at("location", default: none) == none { "" } else { entry.location }
      } else { labels.modalities.at(entry.modality) }
      let location = if entry.at("modality", default: none) == none { "" } else { if entry.at("location", default: none) == none { "" } else { entry.location } }
      block(sticky: true, grid(
        columns: (1fr, 1fr),
        align(left)[#strong(plain(display-company(entry)))#contractor-mark(entry) \ #emph(entry.title)],
        align(right)[#strong(entry-dates(entry)) \ #emph[#modality#if location != "" [#sym.dash.em #location]]],
      ))
      v(2pt)
      if entry.bullets.len() > 0 {
        block(above: 6pt, below: 11pt, pad(left: 1.5em, list(indent: 0.25em, spacing: 0.8em, ..entry.bullets.map(bullet => plain(bullet)))))
      }
    }
  ]
}

#if earlier-experience.len() > 0 {
  mysection(labels.earlier_experience)[
    #set par(justify: false)
    #for title in earlier-experience.map(entry => entry.title).dedup() {
      let entries = earlier-experience.filter(entry => entry.title == title)
      grid(
        columns: (11em, 1fr),
        column-gutter: 1em,
        align(left, text(hyphenate: false, strong(plain(title)))),
        align(left, entries.map(entry =>
          box[#strong(plain(display-company(entry)))#contractor-mark(entry)~#box[(#entry-dates(entry))]]
        ).join(if entries.map(entry => entry.at("earlier_layout", default: none)).contains("lines") { linebreak() } else { [; ] })),
      )
      v(3pt)
    }
  ]
}

#let education-list = [
    #for entry in p.education {
      edu(
        institution: entry.institution,
        degree: entry.degree,
        columns: (1fr, auto),
        dates: if entry.start == none and entry.end == none { "" } else { dates-helper(start-date: if entry.start == none { "" } else { entry.start }, end-date: if entry.end == none { "" } else { entry.end }) },
        location: if p.at("location", default: none) == none { "" } else { p.at("location", default: none) },
      )[]
    }
    #v(8pt)
  ]

#let skill-list = if p.skills.len() > 0 { skills[
  #set par(justify: false)
  #for group in p.skills {
    if type(group) == str {
      [- #plain(group)]
    } else {
      [#strong(plain(group.label)): #plain(group.items.join(", "))]
    }
    v(0.4em)
  }
  #v(8pt)
] }
#let language-list = if p.languages.len() > 0 { languages[
  #for lang in p.languages {
    if type(lang) == str {
      grid(columns: (auto, 1fr), gutter: 0.8em, align(left)[*#plain(lang):*], [])
    } else {
      grid(columns: (auto, 1fr), gutter: 0.8em, align(left)[*#lang.name:*], align(left, if lang.at("level", default: none) == none { [] } else { plain(lang.level) }))
    }
  }
  #v(8pt)
] }


#let certification-list = [
    #set par(justify: false)
    #for entry in p.certifications {
      if type(entry) == str {
        grid(columns: (1fr, auto), align(left)[*#plain(entry)*], [])
      } else {
        let date = if entry.at("expires", default: none) == none { if entry.at("issued", default: none) == none { "" } else { entry.issued } } else { dates-helper(start-date: entry.issued, end-date: entry.expires) }
        grid(
          columns: (1fr, auto),
          column-gutter: 0.8em,
          align(left)[*#plain(entry.name)*#if entry.at("issuer", default: none) == none { [] } else { [, #emph(entry.issuer)] }],
          align(right, date),
        )
        v(0.3em)
      }
    }
    #v(8pt)
  ]

#if p.education.len() > 0 and p.languages.len() > 0 {
  grid(columns: (1fr, 1fr), gutter: 2em,
    mysection(labels.education)[#education-list],
    mysection(labels.languages)[#language-list],
  )
} else {
  if p.education.len() > 0 { mysection(labels.education)[#education-list] }
  if p.languages.len() > 0 { mysection(labels.languages)[#language-list] }
}

#if p.certifications.len() > 0 and p.skills.len() > 0 {
  grid(columns: (1fr, 1fr), gutter: 2em,
    mysection(labels.certifications)[#certification-list],
    mysection(labels.skills)[#skill-list],
  )
} else {
  if p.certifications.len() > 0 { mysection(labels.certifications)[#certification-list] }
  if p.skills.len() > 0 { mysection(labels.skills)[#skill-list] }
}

#if p.at("achievements", default: ()).len() > 0 {
  mysection(labels.achievements)[
    #list(indent: 0.25em, spacing: 0.8em, ..p.achievements.map(plain))
  ]
}
