import plexapi.library
import plexapi.server

from libs.emby import Emby
from setup_auth import setup_auth


# Global Config Vars
SECTIONS_TO_SYNC = []
USERS_TO_SYNC = []


def main():
    """Main handler, sets up connections to Plex and Emby, sets up auth, and pulls in sections."""
    # Get auth info
    auth_info = setup_auth()

    plex_url = auth_info["PLEX_URL"]
    del auth_info["PLEX_URL"]
    emby_url = auth_info["EMBY_URL"]
    del auth_info["EMBY_URL"]
    emby_api_key = auth_info["EMBY_API_KEY"]
    del auth_info["EMBY_API_KEY"]

    for user, credentials in auth_info.items():
        if USERS_TO_SYNC and user not in USERS_TO_SYNC:
            continue

        print(f"\n\nBeginning sync for {user}...")

        emby = Emby(server=emby_url, api_key=emby_api_key, user_id=credentials["Emby"])
        plex = plexapi.server.PlexServer(token=credentials["Plex"], baseurl=plex_url)
        sections = plex.library.sections()

        for section in sections:
            if section.title in SECTIONS_TO_SYNC or not SECTIONS_TO_SYNC:
                if type(section) is plexapi.library.MovieSection:
                    print(f"\n\n\tProcessing Movie section: {section.title}, {len(section.all())} items...")
                    process_movie_section(emby, section)
                elif type(section) is plexapi.library.ShowSection:
                    print(f"\n\n\tProcessing Show section: {section.title}, {len(section.all())} items...")
                    process_show_section(emby, section)


def process_movie_section(emby: Emby, section: plexapi.library.MovieSection):
    """
    Process a Plex movie section. Loops through all movies in the section and marks those that are watched
    as viewed in Emby.

    :param emby: Emby api object connected to the Emby server to update
    :type emby: Emby
    :param section: Plex MovieSection object to process
    :type section: plexapi.library.MovieSection
    """
    updated_count = 0

    emby_section = emby.find_section(section.title)

    if not emby_section:
        print(f"\t\tFailed to find section in Emby matching {section.title}, skipping...")
        return

    for movie in section.all():
        # Skip movie processing if it is not watched
        if not movie.isWatched:
            continue

        # Get provider ID for movie to find in emby
        plex_id = movie.guid

        # Handle new plex movie agent by checking alternative
        if plex_id.startswith("plex://movie/"):
            if len(movie.guids) > 0:
                # print(f"\t\tPlex Movie agent detected for {plex_id}, using alternate: {movie.guids[0].id}")
                plex_id = movie.guids[0].id
            else:
                print(f"\t\tPlex Movie agent detected for {plex_id}, no alternative found, skipping...")
                continue

        provider = ""
        provider_id = ""

        if plex_id.startswith("local") or "agents.none" in plex_id:
            # Unmatched item, skip
            print(f"\t\tMovie [{movie.title} ({movie.year})]: PlexID ({plex_id}) is unmatched, ignoring...")
            continue
        elif "imdb" in plex_id:
            provider_id = plex_id.split("//")[1]
            provider_id = provider_id.split("?")[0]
            provider = "imdb"
        elif "themoviedb" in plex_id or "tmdb" in plex_id:
            provider_id = plex_id.split("//")[1]
            provider_id = provider_id.split("?")[0]
            provider = "tmdb"
        else:
            print(f"\t\tMovie [{movie.title} ({movie.year})]: PlexID ({plex_id}) is unrecognized, ignoring...")
            continue

        # Sync watch status from plex to emby
        if movie.isWatched:
            emby_id = emby.find_item_id(provider, provider_id, emby_section)

            if emby_id:
                emby.mark_item_watched(emby_id)
                updated_count += 1
            else:
                print(f"\t\tFailed to find movie [{movie.title} ({movie.year})] in Emby, skipping...")

    print(f"\t\tFinished processing section, updated status of {updated_count} movies.")


def process_show_section(emby: Emby, section: plexapi.library.ShowSection):
    """
    Process a Plex TV section. Loops through all shows and episodes in the section and marks those that are watched
    as viewed in Emby.

    :param emby: Emby api object connected to the Emby server to update
    :type emby: Emby
    :param section: Plex ShowSection object to process
    :type section: plexapi.library.ShowSection
    """
    updated_count = 0

    emby_section = emby.find_section(section.title)

    if not emby_section:
        print(f"\t\tFailed to find section in Emby matching {section.title}, skipping...")
        return

    for show in section.all():
        # Skip show if no episodes of it have been viewed
        if show.viewCount < 1:
            continue

        # Get provider ID for show to find in emby
        plex_id = show.guid

        provider = ""
        provider_id = ""

        if plex_id.startswith("local") or "agents.none" in plex_id:
            # Unmatched item, skip
            print(f"\t\tShow [{show.title} ({show.year})]: PlexID ({plex_id}) is unmatched, ignoring...")
            continue
        elif "thetvdb" in plex_id:
            provider_id = plex_id.split("//")[1]
            provider_id = provider_id.split("?")[0]
            provider = "tvdb"
        elif "themoviedb" in plex_id or "tmbd" in plex_id:
            provider_id = plex_id.split("//")[1]
            provider_id = provider_id.split("?")[0]
            provider = "tmdb"
        else:
            print(f"\t\tShow [{show.title} ({ show.year})]: PlexID ({plex_id}) is unrecognized, ignoring...")
            continue

        # Find show in emby
        emby_show_id = emby.find_item_id(provider, provider_id, emby_section)

        if not emby_show_id:
            print(f"\t\tFailed to find show [{show.title} ({show.year})] in Emby, skipping...")
            continue

        # Get episodes from emby
        emby_episodes = emby.get_show_episodes(emby_section, emby_show_id)

        if not emby_episodes:
            print(f"\t\tFailed to find episodes in emby for show [{show.title} ({show.year})], skipping...")
            continue

        updated_count += 1

        # Loop over episodes syncing watched status
        for episode in show.episodes():
            if episode.isWatched:
                try:
                    emby_episode_id = emby_episodes[int(episode.parentIndex)][int(episode.index)]
                except KeyError:
                    print(
                        (
                            f"\t\tFailed to find episode S{episode.parentIndex}E{episode.index} of "
                            f"show {show.title} in Emby, skipping..."
                        )
                    )
                    continue

                emby.mark_item_watched(emby_episode_id)

    print(f"\t\tFinished processing section, updated status of {updated_count} shows.")


if __name__ == "__main__":
    main()
