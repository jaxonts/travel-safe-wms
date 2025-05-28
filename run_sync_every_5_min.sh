while true; do
    echo "[ $(date) ] Running eBay sync..."
    python manage.py sync_ebay_active_listings
    echo "[ $(date) ] Done. Sleeping for 5 minutes."
    sleep 300
done
