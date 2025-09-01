# Link Header

```plain
# As per RFC can just add new link headers on the end
# https://github.com/psf/requests/issues/741#issuecomment-7294344
# There's two different popular headers for this
# https://www.rfc-editor.org/rfc/rfc5988#section-6.2.2
# https://www.rfc-editor.org/rfc/rfc8631#section-6.2
response.headers.append("Link", f'<{openapi_url}>; rel="service-desc"')
response.headers.append("Link", f'<{openapi_url}>; rel="describedby"')
response.headers.append("Link", f'<{docs_url}>; rel="service-doc"')
response.headers.append("Link", f'<{docs_url}>; rel="help"')
```

These pagination headers **may** be present on a response. If not, all the data fit onto one page (or the server doesn't support pagination). If pagination **did** occur, the page size is up to the server.

```plain
Link: <https://example.com/orgs?cursor=MTYwMTk>; rel="next",
<https://example.com/orgs?cursor=EMZkdE>; rel="prev"
```

## Rels

### All Responses

* `service-desc`
  * Identifies service description for the context that is primarily intended for consumption by machines.
  * links to openapi.json
* `describedby`
  * Why do we use this one?
  * links to openapi.json
* `service-doc`
  * Identifies service documentation for the context that is primarily intended for human consumption.
  * links to documentation
* `help`
  * Why do we use this one?
  * links to documentation

### Pagination

* `first` - first page of results
* `last` - last page of results
* `next` - next page of results
* `prev` - previous page of results

## References

* <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Link>
* <https://www.rfc-editor.org/rfc/rfc8631.html>
* <https://www.iana.org/assignments/link-relations/link-relations.xhtml>
* <https://docs.github.com/en/enterprise-cloud@latest/rest/using-the-rest-api/using-pagination-in-the-rest-api#using-link-headers>
