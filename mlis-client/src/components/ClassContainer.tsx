import * as React from 'react';
import { createRefetchContainer, RelayRefetchProp } from 'react-relay';
import { graphql } from 'babel-plugin-relay/macro';
import { ClassContainer_main } from './__generated__/ClassContainer_main.graphql';
import Authorized from './Authorized';
import Panel from 'react-bootstrap/lib/Panel';
import { Link } from 'react-router-dom';
import { viewerIsClassMentor, viewerCanAccessClass } from '../utils';
import { Comments } from 'react-facebook';
import MentorToolsPage from './MentorToolsPage';

interface Props {
  relay: RelayRefetchProp,
  main: ClassContainer_main,
}
interface State {
  mentorToolsOpen: boolean,
}

class ClassContainer extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      mentorToolsOpen: false
    };
  }
  renderMentorTool() {
    if (!this.state.mentorToolsOpen) {
      return null;
    }
    return (
      <MentorToolsPage id={this.props.main.viewer!.class.id} />
    )
  }
  renderClass() {
    if (this.props.main.viewer == null) {
      return null;
    }
    const viewer = this.props.main.viewer;
    const viewerIsMentor = viewerIsClassMentor(viewer, viewer.class);
    const viewerCanAccess = viewerCanAccessClass(viewer, viewer.class);
    let body = null;
    if (viewerCanAccess) {
      body = (
        <div>
          Mentor: <Link to={`/user/${viewer.class.mentor.id}`}>{viewer.class.mentor.name}</Link>
        </div>
      );
    } else if (viewer.class.viewerIsEleminated) {
      body = (
        <div>
          You have been eleminated from a class, most lickly you missed task deadline
        </div>
      );
    } else if (!viewer.class.viewerIsApplied) {
      body = (
        <div>
          You not in the class, you can apply for classes <Link to='/classes'>here</Link>
        </div>
      );
    }
    let mentorTools = null;
    if (viewerIsMentor) {
      mentorTools = (
        <Panel
          onToggle={() => this.setState({ mentorToolsOpen: !this.state.mentorToolsOpen })}
          expanded={this.state.mentorToolsOpen}>
          <Panel.Heading>
            <Panel.Title>
              <Panel.Toggle>
                Open mentor tools
              </Panel.Toggle>
            </Panel.Title>
          </Panel.Heading>
          <Panel.Collapse>
            {this.renderMentorTool.bind(this)()}
          </Panel.Collapse>
        </Panel>
      )
    }
    return (
      <Panel>
        <Panel.Body>
          <h1>MLIS Class {new Date(viewer.class.startAt).toLocaleDateString()}</h1>
          <h2>{viewer.class.name}</h2>
          {body}
          {mentorTools}
          <Comments href={window.location.href.split('?')[0]} width="100%" />
        </Panel.Body>
      </Panel>
    );
  }
  render() {
    return (
      <Authorized main={this.props.main} mainRelay={this.props.relay}>
        {this.renderClass()}
      </Authorized>
    );
  }
}

export default createRefetchContainer(
    ClassContainer,
    {
      main: graphql`
        fragment ClassContainer_main on Main @argumentDefinitions(
          id: { type: "ID!" }
        ) {
          ...Authorized_main
          viewer {
            user {
              id
            }
            class(id:$id) {
              id
              startAt
              name
              mentor {
                id
                name
              }
              viewerIsApplied
              viewerIsEleminated
            }
          }
        }`,
    },
    graphql`
      query ClassContainerQuery($id: ID!) {
        main {
          ...ClassContainer_main @arguments(id: $id)
        }
      }`
);