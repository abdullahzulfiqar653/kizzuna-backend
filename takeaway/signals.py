from tag.models import Tag


def takeaway_tags_changed(sender, action, instance, reverse, pk_set, **kwargs):
    if reverse:
        tag = instance
    elif pk_set:
        tag_id = next(iter(pk_set))
        tag = Tag.objects.get(id=tag_id)
    else:  # not reverse and len(pk_set) == 0
        # This happens when tag is already in takeaway.tags
        # so no tag is added.
        return

    if action in ("post_add", "post_remove"):
        tag.takeaway_count = tag.takeaways.count()
        if tag.takeaway_count > 0:
            tag.save()
        else:  # tag.takeaway_count == 0
            tag.delete()
